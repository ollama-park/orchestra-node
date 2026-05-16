import sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "messages"))

import json
import grpc
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random

from messages import message_pb2
from messages import message_pb2_grpc

SERVER_ADDR = "172.16.45.1:9000"
# SERVER_ADDR = "127.0.0.1:9000"

THREADS = 4


def fake_llm_response(payload_str: str) -> str:
    """
    Simulates LLM response instead of calling ASK service.
    payload_str is a JSON string: {"context": [...], "request": "..."}
    Returns a JSON string: {"goal_targets": [...], "main_response": "...", "steps": [...]}
    """
    try:
        payload = json.loads(payload_str)
        request_text = payload.get("request", "")
        objects = [obj["object_name"] for obj in payload.get("context", [])]
    except (json.JSONDecodeError, KeyError):
        request_text = payload_str
        objects = []

    # Simulate latency
    time.sleep(random.uniform(0.2, 1.0))

    # Pick 1-2 random objects as fake targets
    targets = random.sample(objects, k=min(random.randint(1, 2), len(objects))) if objects else []

    fake_steps = [
        {"step": f"Locate the {targets[0]}"},
        {"step": "Verify the status indicator"},
        {"step": f"Respond to: {request_text[:40]}"},
    ] if targets else [
        {"step": f"Process request: {request_text[:40]}"},
    ]

    return json.dumps({
        "goal_targets": targets,
        "main_response": f"(mock) Handling '{request_text}' with objects: {objects}",
        "steps": fake_steps,
    })


def worker(worker_id: int):
    channel = grpc.insecure_channel(SERVER_ADDR)
    stub = message_pb2_grpc.MessageServiceStub(channel)

    print(f"[test worker {worker_id}] started")

    while True:
        try:
            task = stub.GetTask(message_pb2.Empty())

            if task.id:
                print(f"[test worker {worker_id}] received: {task.text}")

                # Instead of calling the real ASK gRPC → fake structured response
                result = fake_llm_response(task.text)

                print(f"[test worker {worker_id}] result: {result}")

                stub.SendResult(
                    message_pb2.ResultRequest(
                        id=task.id,
                        text=result
                    )
                )
            else:
                time.sleep(1)

        except Exception as e:
            print(f"[test worker {worker_id}] error:", e)
            time.sleep(2)


def main():
    print(f"Test processor started with {THREADS} threads")

    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        for i in range(THREADS):
            executor.submit(worker, i)

        threading.Event().wait()


if __name__ == "__main__":
    main()
