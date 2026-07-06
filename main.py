from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict, deque
import uuid
import time

app = FastAPI()

EMAIL = "23f2001375@ds.study.iitm.ac.in"

# -----------------------------
# CORS
# -----------------------------
ALLOWED_ORIGINS = [
    "https://app-i52wzh.example.com",
    "https://exam.sanand.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# -----------------------------
# Rate Limiter
# -----------------------------
RATE_LIMIT = 14
WINDOW = 10
buckets = defaultdict(deque)

# -----------------------------
# Request Context + Rate Limiter
# -----------------------------
@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):
    # Request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    # Client ID
    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    bucket = buckets[client]

    # Remove expired timestamps
    while bucket and now - bucket[0] >= WINDOW:
        bucket.popleft()

    # Rate limit check
    if len(bucket) >= RATE_LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["X-Request-ID"] = request_id
        return response

    bucket.append(now)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# -----------------------------
# Endpoint
# -----------------------------
@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }