from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.routers import auth, databases, configs, sync
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NotionShare API",
    description="API for sharing filtered Notion database views",
    version="1.0.0"
)

# Custom CORS middleware for development
class SimpleCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle preflight
        if request.method == "OPTIONS":
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "600",
                },
            )

        # Handle actual request
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

# Use custom CORS middleware
app.add_middleware(SimpleCORSMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(databases.router, prefix="/api/v1")
app.include_router(configs.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "NotionShare API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
