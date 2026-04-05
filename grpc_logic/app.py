import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "messages"))

import grpc
import asyncio
from concurrent import futures
import threading
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from messages import message_pb2
from messages import message_pb2_grpc

requests = {}
responses = {}

# --- gRPC Service ---

class MessageService(message_pb2_grpc.MessageServiceServicer):
    def GetTask(self, request, context):
        for task_id, text in list(requests.items()):
            del requests[task_id]
            return message_pb2.TaskReply(id=task_id, text=text)
        return message_pb2.TaskReply(id="", text="")

    def SendResult(self, request, context):
        responses[request.id] = request.text
        print("Result received:", request.text)
        return message_pb2.Empty()

def run_grpc():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    message_pb2_grpc.add_MessageServiceServicer_to_server(MessageService(), server)
    server.add_insecure_port("172.16.45.1:9000")
    server.start()
    print("gRPC server running on :9000")
    server.wait_for_termination()

# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    grpc_thread = threading.Thread(target=run_grpc, daemon=True)
    grpc_thread.start()
    yield

app = FastAPI(lifespan=lifespan)

# --- Request schema ---

class UserRequest(BaseModel):
    userRequest: str

# --- Main endpoint for Unity frontend ---

@app.post("/help")
async def chat(body: UserRequest):
    task_id = str(uuid.uuid4())
    requests[task_id] = body.userRequest

    result = await wait_for_result(task_id)
    return {"llmResponse": result}

async def wait_for_result(task_id: str, poll_interval: float = 0.3, timeout: float = 60.0) -> str:
    elapsed = 0.0
    while elapsed < timeout:
        if task_id in responses:
            return responses.pop(task_id)
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    return "Error: request timed out"
