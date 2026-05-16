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

from messages import message_pb2
from messages import message_pb2_grpc

# Asshole VPS
SERVER_ADDR = "172.16.45.1:9000"      # app.py
# ip r | grep default
ASK_ADDR = "<your_windows_ip>:50051"     # Windows service

THREADS = 4


def worker(worker_id: int):

    channel = grpc.insecure_channel(SERVER_ADDR)
    stub = message_pb2_grpc.MessageServiceStub(channel)

    ask_channel = grpc.insecure_channel(ASK_ADDR)
    ask_stub = message_pb2_grpc.MessageServiceStub(ask_channel)

    print(f"Worker {worker_id} started")

    while True:
        try:
            task = stub.GetTask(message_pb2.Empty())

            if task.id:
                print(f"[worker {worker_id}] received task {task.id}")

                # task.text is the full JSON payload:
                # {"context": [...], "request": "..."}
                # Forward it as-is to the Windows AI service
                response = ask_stub.ProcessTask(
                    message_pb2.TaskReply(
                        id=task.id,
                        text=task.text
                    )
                )

                # response.text must be a JSON string with this shape:
                # {
                #   "goal_targets": ["object_name", ...],
                #   "main_response": "...",
                #   "steps": [{"step": "..."}, ...]
                # }
                #
                # Validate it before sending back so app.py gets clean JSON.
                try:
                    parsed = json.loads(response.text)
                    result_str = json.dumps({
                        "goal_targets": parsed.get("goal_targets", []),
                        "main_response": parsed.get("main_response", ""),
                        "steps": parsed.get("steps", []),
                    })
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"[worker {worker_id}] bad AI response: {e}")
                    result_str = json.dumps({
                        "goal_targets": [],
                        "main_response": response.text or "Error: no response",
                        "steps": [],
                    })

                stub.SendResult(
                    message_pb2.ResultRequest(
                        id=task.id,
                        text=result_str
                    )
                )

            else:
                time.sleep(1)

        except Exception as e:
            print(f"[worker {worker_id}] error:", e)
            time.sleep(2)


def main():

    print(f"Processor started with {THREADS} threads")

    with ThreadPoolExecutor(max_workers=THREADS) as executor:

        for i in range(THREADS):
            executor.submit(worker, i)

        threading.Event().wait()


if __name__ == "__main__":
    main()
