import os
import uuid
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.schema import HumanMessage, AIMessage
from langchain.schema.runnable import RunnableConfig
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
import sqlite3
import time
from app.routes import router
from app.utils import init_db
from collections import defaultdict
import boto3
from datetime import datetime
from app.models import MessageIn, MessageCreateRequest, MessageOut, Session, UploadTextRequest, CreateSessionRequest, RenameSessionRequest, FavoriteSessionRequest, Message, RAGRequest
from app.middleware import APIKeyMiddleware
from app.vector_store import vectorstore, qa_chain
from app.utils import check_rate_limit, add_message_internal, to_message_out

load_dotenv()

API_KEY = os.getenv("API_KEY")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # default fallback

BEDROCK_CHAT_MODEL = os.getenv("BEDROCK_CHAT_MODEL", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
BEDROCK_EMBEDDING_MODEL = os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v1")

AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")

AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")



DB_FILE = os.getenv("DB_FILE", "chat_history.db")

RATE_LIMIT = int(os.getenv("RATE_LIMIT", 100))
RATE_WINDOW = int(os.getenv("RATE_WINDOW", 60))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

app = FastAPI()
logger = logging.getLogger("uvicorn.error")



app.add_middleware(APIKeyMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


init_db()

app.include_router(router)

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})