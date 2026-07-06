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
    # Exam page origin (keep this)
    "https://exam.sanand.workers.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Rate Limiter
# -----------------------------
RATE_LIMIT = 14
WINDOW = 10

buckets = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()
    q = buckets[client]

    while q and now - q[0] > WINDOW:
        q.popleft()

    if len(q) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    q.append(now)

    response = await call_next(request)
    return response


# -----------------------------
# Request Context Middleware
# -----------------------------
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

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