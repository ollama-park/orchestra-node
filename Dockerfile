FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Regenerate protobuf stubs at build time so versions always match
RUN python -m grpc_tools.protoc \
    -I messages \
    --python_out=messages \
    --grpc_python_out=messages \
    messages/message.proto

EXPOSE 8000 9000

CMD ["uvicorn", "grpc_logic.app:app", "--host", "0.0.0.0", "--port", "8000"]