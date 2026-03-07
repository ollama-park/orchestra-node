import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "messages"))

import grpc
import time

from messages import message_pb2
from messages import message_pb2_grpc


channel = grpc.insecure_channel("127.0.0.1:9000")
stub = message_pb2_grpc.MessageServiceStub(channel)

print("Processor started...")


while True:

    task = stub.GetTask(message_pb2.Empty())

    if task.id:

        print("Processing:", task.text)

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
