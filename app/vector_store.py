from langchain_aws import ChatBedrock
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
import os
import boto3
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1") 

BEDROCK_CHAT_MODEL = os.getenv("BEDROCK_CHAT_MODEL", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
BEDROCK_EMBEDDING_MODEL = os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v1")

AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")

AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")

VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "faiss_index")

bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION, 
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

embedding = BedrockEmbeddings(
    model_id=BEDROCK_EMBEDDING_MODEL,
    client=bedrock_client,

)

if os.path.exists(VECTOR_STORE_DIR):
    vectorstore = FAISS.load_local(
    VECTOR_STORE_DIR,
    embedding,
    allow_dangerous_deserialization=True 
    )
else:
    vectorstore = FAISS.from_texts(["init"], embedding)
    vectorstore.save_local(VECTOR_STORE_DIR)

retriever = vectorstore.as_retriever()
llm = ChatBedrock(
        model_id=BEDROCK_CHAT_MODEL,
        client=bedrock_client,
        model_kwargs={
            "temperature": 0.1,
            "max_tokens": 131072,
            "top_k": 50,
            "top_p":0.999
        },
    )
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
)