# RAG Chat Microservice

A lightweight FastAPI + SQLite microservice with Retrieval-Augmented Generation (RAG) logic using LangChain and AWS Bedrock. Fully containerized with Docker.

---

## Features

- Create, list, rename, favorite, delete chat sessions  
- Add and retrieve messages per session  
- RAG endpoint powered by LangChain + AWS Bedrock  
- SQLite persistence with optional mapped volume  
- Built-in rate-limiting and API key auth via middleware  
- Dockerized for local or cloud deployment  

---

## Docker Setup

### Build the Docker image
```bash
docker build -t rag-chat-microservice .
```

### Run the container
```bash
docker run -d -p 8000:8000 -v "${PWD}/chat_history.db:/app/chat_history.db" --env-file .env --name ragchat rag-chat-microservice
```

### API Endpoints
| Endpoint                       | Description                                 |
| ------------------------------ | ------------------------------------------- |
| `POST /session`                | Create a new session.                       |
| `GET /sessions`                | List all existing sessions.                 |
| `POST /session/{sid}/rename`   | Rename an existing session.                 |
| `POST /session/{sid}/favorite` | Mark session as favorite.                   |
| `DELETE /session/{sid}`        | Delete session and associated messages.     |
| `POST /session/{sid}/message`  | Add a message to a session.                 |
| `GET /session/{sid}/messages`  | Retrieve message history.                   |
| `POST /rag/{sid}`              | Send a new user query and get RAG response. |

### Example
curl -X POST http://127.0.0.1:8000/session \
  -H "X-API-KEY: some_secure_api_key" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Test Session\"}"

### Prerequisite
Docker installed on your machine
.env file located in project root, containing at least:
    API_KEY=some_secure_api_key
    AWS_* credentials
    VECTOR_STORE_DIR=faiss_index

### Project Structure
.
├── Dockerfile
├── requirements.txt
├── .env
├── chat_history.db   
└── app/
    ├── main.py           # app factory & middleware configuration
    ├── routes.py         # API endpoints using FastAPI router
    ├── models.py         # Pydantic schemas
    ├── utils.py          # helper functions (rate limiting, db helpers)
    ├── vector_store.py   # LangChain retrieval + QA setup
    └── middleware.py     # API key auth middleware


### Local Running (without Docker)
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

Access docs at http://127.0.0.1:8000/docs.