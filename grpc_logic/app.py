import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "messages"))

import os
import json
import grpc
import asyncio
from concurrent import futures
import threading
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from messages import message_pb2
from messages import message_pb2_grpc

# --- Config from environment (with sane defaults) ---
GRPC_HOST = os.getenv("GRPC_HOST", "0.0.0.0")
GRPC_PORT = os.getenv("GRPC_PORT", "9000")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://ar.totatato.com").split(",")

requests: dict[str, str] = {}
responses: dict[str, str] = {}
lock = threading.Lock()

# --- gRPC Service ---

class MessageService(message_pb2_grpc.MessageServiceServicer):
    def GetTask(self, request, context):
        with lock:
            for task_id, text in list(requests.items()):
                del requests[task_id]
                return message_pb2.TaskReply(id=task_id, text=text)
        return message_pb2.TaskReply(id="", text="")

    def SendResult(self, request, context):
        with lock:
            responses[request.id] = request.text
        print(f"[gRPC] Result received for {request.id}: {request.text[:80]}")
        return message_pb2.Empty()

def run_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    message_pb2_grpc.add_MessageServiceServicer_to_server(MessageService(), server)
    bind_addr = f"{GRPC_HOST}:{GRPC_PORT}"
    server.add_insecure_port(bind_addr)
    server.start()
    print(f"[gRPC] Server running on {bind_addr}")
    server.wait_for_termination()

# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    grpc_thread = threading.Thread(target=run_grpc, daemon=True)
    grpc_thread.start()
    yield

app = FastAPI(lifespan=lifespan)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# --- Request / Response schemas ---

class SceneObject(BaseModel):
    object_name: str
    positionX: float
    positionY: float
    positionZ: float

class UserRequest(BaseModel):
    context: List[SceneObject]
    request: str

class StepItem(BaseModel):
    step: str

class AssistantResponse(BaseModel):
    goal_targets: List[str]
    main_response: str
    steps: List[StepItem]

# --- Main endpoint ---

@app.post("/help", response_model=AssistantResponse)
async def chat(body: UserRequest):
    task_id = str(uuid.uuid4())

    # Serialize the full request as JSON to send through gRPC
    payload_str = json.dumps(body.model_dump())

    with lock:
        requests[task_id] = payload_str

    raw_result = await wait_for_result(task_id)

    # Parse the JSON response from the AI worker
    try:
        result = json.loads(raw_result)
        return AssistantResponse(
            goal_targets=result.get("goal_targets", []),
            main_response=result.get("main_response", ""),
            steps=[StepItem(step=s["step"]) for s in result.get("steps", [])],
        )
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[app] Failed to parse AI response: {e}\nRaw: {raw_result}")
        return AssistantResponse(
            goal_targets=[],
            main_response=raw_result,
            steps=[],
        )

@app.get("/health")
async def health():
    return {"status": "ok"}

async def wait_for_result(
    task_id: str,
    poll_interval: float = 0.3,
    timeout: float = 60.0
) -> str:
    elapsed = 0.0
    while elapsed < timeout:
        with lock:
            if task_id in responses:
                return responses.pop(task_id)
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    with lock:
        requests.pop(task_id, None)
    return '{"goal_targets": [], "main_response": "Error: request timed out", "steps": []}'
