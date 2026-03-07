import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "messages"))

import grpc
from concurrent import futures
import threading
import uuid

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from messages import message_pb2
from messages import message_pb2_grpc


requests = {}
responses = {}


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

    server.add_insecure_port("0.0.0.0:9000")
    server.start()
    server.wait_for_termination()


app = FastAPI()


@app.post("/send")
def send(text: str):
    task_id = str(uuid.uuid4())
    requests[task_id] = text
    return {"task_id": task_id}


@app.get("/result/{task_id}")
def result(task_id: str):
    return {"result": responses.get(task_id)}


@app.get("/", response_class=HTMLResponse)
def ui():
    return """
<html>
<body>

<h2>Send message</h2>

<input id="text">
<button onclick="send()">Send</button>

<h3>Result:</h3>
<div id="result">Waiting...</div>

<script>

let taskId = null

async function send(){
    const text = document.getElementById("text").value

    const r = await fetch("/send?text=" + encodeURIComponent(text), {
        method:"POST"
    })

    const j = await r.json()
    taskId = j.task_id

    poll()
}

async function poll(){
    if(!taskId) return

    const r = await fetch("/result/" + taskId)
    const j = await r.json()

    if(j.result){
        document.getElementById("result").innerText = j.result
    }else{
        setTimeout(poll,1000)
    }
}

</script>

</body>
</html>
"""


if __name__ == "__main__":
    t = threading.Thread(target=run_grpc, daemon=True)
    t.start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
