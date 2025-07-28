import sqlite3
import uuid
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from langchain.schema import HumanMessage, AIMessage
from langchain.schema.runnable import RunnableConfig
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
import os
from dotenv import load_dotenv
from app.models import (
    Session, CreateSessionRequest, RenameSessionRequest, FavoriteSessionRequest,
    MessageCreateRequest, MessageOut, Message, RAGRequest, MessageIn, UploadTextRequest
)
from app.utils import add_message_internal, to_message_out, check_rate_limit
from app.vector_store import vectorstore, qa_chain

router = APIRouter()

load_dotenv()

VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "faiss_index")
DB_FILE = os.getenv("DB_FILE", "chat_history.db")

@router.post("/session", response_model=Session)
async def create_session(request: CreateSessionRequest):
    sid = str(uuid.uuid4())
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("INSERT INTO sessions (id,name,is_favorite) VALUES (?,?,?)", (sid, request.name, False))
    return Session(id=sid, name=request.name, is_favorite=False)

@router.get("/sessions", response_model=List[Session])
def list_sessions():
    with sqlite3.connect(DB_FILE) as conn:
        result = conn.execute("SELECT id, name, is_favorite FROM sessions").fetchall()
    return [Session(id=row[0], name=row[1], is_favorite=row[2]) for row in result]

@router.post("/session/{sid}/rename", response_model=Session)
async def rename_session(sid: str, data: RenameSessionRequest):
    new_name = data.new_name
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE sessions SET name = ? WHERE id = ?", (new_name, sid))
        conn.commit()
        row = conn.execute("SELECT id, name, is_favorite FROM sessions WHERE id = ?", (sid,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    updated_session = Session(id=row[0], name=row[1], is_favorite=bool(row[2]))
    return updated_session


@router.post("/session/{sid}/favorite", response_model=Session)
async def favorite_session(sid: str, data: FavoriteSessionRequest):
    fav = data.is_favorite
    with sqlite3.connect(DB_FILE) as conn:
        result = conn.execute("UPDATE sessions SET is_favorite = ? WHERE id = ?", (fav, sid))
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        row = conn.execute("SELECT id, name, is_favorite FROM sessions WHERE id = ?", (sid,)).fetchone()
    return Session(id=row[0], name=row[1], is_favorite=bool(row[2]))

@router.delete("/session/{sid}")
def delete_session(sid: str):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
        conn.execute("DELETE FROM sessions WHERE id = ?", (sid,))
    return {"status": "deleted"}

@router.post("/session/{sid}/message", response_model=Message)
async def add_message(sid: str, req: MessageCreateRequest):
    return await add_message_internal(sid, req.sender, req.content)

@router.get("/session/{sid}/messages", response_model=List[MessageOut])
async def get_messages(sid: str):
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute("SELECT id, sender, content, timestamp FROM messages WHERE session_id=?", (sid,)).fetchall()
    return [to_message_out(row) for row in rows]


@router.post("/rag/{sid}")
async def rag_response(sid: str, req: RAGRequest):
    user_message = req.user_message
    check_rate_limit(sid)
    with sqlite3.connect(DB_FILE) as conn:
        rows = conn.execute("SELECT sender, content FROM messages WHERE session_id = ? ORDER BY timestamp", (sid,)).fetchall()
    chat_history = []
    for sender, content in rows:
        chat_history.append(HumanMessage(content=content) if sender.lower()=="user" else AIMessage(content=content))
    chat_history.append(HumanMessage(content=user_message))
    result = qa_chain.invoke({"query": user_message}, config=RunnableConfig(configurable={"chat_history": chat_history}))
    await add_message_internal(sid, "user", user_message)
    await add_message_internal(sid, "assistant", result.get('result'))
    return {"response": result}

# ------------- Upload Documents --------------------
@router.post("/upload-text")
async def upload_text(data: UploadTextRequest):
    file_path = data.file_path
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail=f"File not found: {file_path}")

    # Try auto-detect encoding to avoid decode errors
    loader = TextLoader(file_path, autodetect_encoding=True)
    try:
        docs = loader.load()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Error loading file: {str(e)}")

    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    chunks = splitter.split_documents(docs)
    if not chunks:
        raise HTTPException(status_code=400, detail="No content to index")

    vectorstore.add_documents(documents=chunks)
    vectorstore.save_local(VECTOR_STORE_DIR)

    return {"status": "uploaded", "chunks_indexed": len(chunks)}