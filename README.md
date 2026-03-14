# Orchestra Node

A small distributed processing demo built with **FastAPI + gRPC**.

The system allows a web UI to submit tasks to a central server.
External processors (workers) poll the server, process the task, and send the result back.

This repository contains two main scripts:

* `app.py` — central orchestration server (FastAPI + gRPC)
* `processor.py` — worker/processor node (AI assistant, Ollama, etc.)

---

# Architecture

```
Browser
   │
   ▼
FastAPI Web UI  (app.py)
   │
   ▼
gRPC Task Queue (app.py)
   ▲
   │
Processor / AI Worker (processor.py)
```

Example deployment:

```
VPS (172.16.45.1)
 ├─ FastAPI UI :8000
 └─ gRPC server :9000

Worker machine (172.16.45.5)
 └─ processor.py
```

---

# Components

## app.py

The **central orchestration server**.

Responsibilities:

* exposes a **web interface**
* receives user prompts
* stores tasks
* exposes a **gRPC server**
* sends tasks to processors
* receives results
* returns results to the browser

Ports:

```
8000 → FastAPI web interface
9000 → gRPC task server
```

The FastAPI application also launches the gRPC server internally using a **lifespan startup hook**.

---

## processor.py

The **worker node**.

Responsibilities:

* connects to the gRPC server
* polls for tasks
* processes requests
* sends results back

The worker uses a **thread pool** to allow multiple concurrent tasks.

Typical configuration:

```
THREADS = 4
```

Each thread:

1. polls the server (`GetTask`)
2. processes the task
3. sends the result (`SendResult`)

Example demo transformation:

```
@@##@@ + input_text
```

In real usage this script can run:

* Ollama
* LLMs
* ML models
* other compute tasks

---

# Repository structure

```
.
├── app.py
├── processor.py
├── messages/
│   ├── message.proto
│   ├── message_pb2.py
│   └── message_pb2_grpc.py
├── requirements.txt
├── shell.nix
└── README.md
```

---

# Installation

Two installation methods are supported.

---

## Option 1 — Python requirements

Install dependencies:

```
pip install -r requirements.txt
```

Dependencies:

```
grpcio
grpcio-tools
fastapi
uvicorn
```

---

## Option 2 — Nix (recommended)

If you use Nix / NixOS:

```
nix-shell
```

This will create a reproducible development environment with all dependencies installed.

---
# IMPORTANT regenerate messages

For each pip install it will have problems with which I am lazy to fight
do it in the root of repository.
```
python -m grpc_tools.protoc \
  -I messages \
  --python_out=messages \
  --grpc_python_out=messages \
  messages/message.proto
```

---

# Running the server

Run the orchestration server:

```
uvicorn app:app --host 0.0.0.0 --port 8000
```

This starts:

```
FastAPI UI  → http://localhost:8000
gRPC server → localhost:9000
```

Open in browser:

```
http://localhost:8000
```

---

# Running the processor

Run the worker:

```
python processor.py
```

The processor will:

1. start a thread pool
2. poll the gRPC server
3. receive tasks
4. process them concurrently
5. send results back

---

# CPU affinity (optional)

You can bind a processor to a specific CPU core using `taskset`.

Example:

```
taskset -c 2 python processor.py
```

This restricts the worker process to **CPU core 2**.

Example multi-core worker cluster:

```
taskset -c 0 python processor.py
taskset -c 1 python processor.py
taskset -c 2 python processor.py
taskset -c 3 python processor.py
```

Each worker runs independently and processes tasks from the same server.

---

# Example workflow

1. Open the web UI
2. Submit a message
3. The task is stored on the server
4. A processor polls the task
5. The processor processes the message
6. The browser receives the result via polling

Example result:

```
Input:  hello
Output: @@##@@hello
```

---

# Scaling

Multiple processors can run simultaneously:

```
        app.py
           │
 ┌─────────┼─────────┐
 │         │         │
worker1  worker2  worker3
```

This allows **horizontal scaling of processing nodes**.

Each worker can also run **multiple threads** internally.

Example:

```
4 processors × 4 threads = 16 concurrent tasks
```

---

# Future improvements

Possible extensions:

* Ollama / LLM integration
* streaming responses
* authentication
* persistent task queue (Redis / Kafka)
* WebSocket responses instead of polling
* GPU worker nodes

---

# License

MIT
