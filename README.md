# Orchestra Node

A small distributed processing demo built with **FastAPI + gRPC**.

This repository contains two main scripts:

* `app.py` — central orchestration server (FastAPI + gRPC)
* `processor.py` — worker/processor node (AI assistant, Ollama, etc.)
* 
Example deployment:

```
VPS (172.16.45.1)
 ├─ FastAPI UI :8000
 └─ gRPC server :9000

Worker machine (172.16.45.5)
 └─ processor.py
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
FastAPI  → http://localhost:8000
gRPC server → localhost:9000
```

---

# Running the processor

Run the worker:

```
python processor.py
```

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

