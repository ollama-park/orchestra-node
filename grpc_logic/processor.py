import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "messages"))

import grpc
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from messages import message_pb2
from messages import message_pb2_grpc


SERVER_ADDR = "127.0.0.1:9000"
THREADS = 4


def worker(worker_id: int):
    """
    Each worker thread maintains its own gRPC channel
    and continuously polls the server for tasks.
    """

    channel = grpc.insecure_channel(SERVER_ADDR)
    stub = message_pb2_grpc.MessageServiceStub(channel)

    print(f"Worker {worker_id} started")

    while True:
        try:
            task = stub.GetTask(message_pb2.Empty())

            if task.id:
                print(f"[worker {worker_id}] Processing: {task.text}")

                # simulate processing (replace with Ollama later)
                time.sleep(2)

                result = "@@##@@" + task.text

                stub.SendResult(
                    message_pb2.ResultRequest(
                        id=task.id,
                        text=result
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

        # keep main thread alive
        threading.Event().wait()


if __name__ == "__main__":
    main()