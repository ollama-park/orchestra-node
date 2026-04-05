import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "messages"))

import grpc
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import random

from messages import message_pb2
from messages import message_pb2_grpc

# Same server
SERVER_ADDR = "172.16.45.1:9000"

THREADS = 4


def fake_llm_response(text: str) -> str:
    """
    Simulates LLM response instead of calling ASK service
    """
    responses = [
        f"Processed: {text}",
        f"Echo: {text}",
        f"LLM says: {text[::-1]}",
        f"Answer to '{text}' is 42",
        f"[mock] {text.upper()}",
    ]

    # simulate latency
    time.sleep(random.uniform(0.2, 1.0))

    return random.choice(responses)


def worker(worker_id: int):

    channel = grpc.insecure_channel(SERVER_ADDR)
    stub = message_pb2_grpc.MessageServiceStub(channel)

    print(f"[test worker {worker_id}] started")

    while True:
        try:
            task = stub.GetTask(message_pb2.Empty())

            if task.id:

                print(f"[test worker {worker_id}] received: {task.text}")

                # 🔥 instead of ASK gRPC → local fake response
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
