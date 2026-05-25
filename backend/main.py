import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import settings
from backend.routes import admin, auth, choices, compare, explore, guidance, logging, payments, rounds, scraping, workspace
from backend.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_runtime()
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Counsly API",
    description="Algorithmic backend service for the 2027 TNEA counseling cycle.",
    version="2027.0",
    lifespan=lifespan,
)

# Robust CORS middleware configuration supporting local and deployed frontend surfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Exception handling boundaries
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected system exception occurred."}
    )

# Register routes
app.include_router(auth.router)
app.include_router(guidance.router)
app.include_router(choices.router)
app.include_router(explore.router)
app.include_router(compare.router)
app.include_router(rounds.router)
app.include_router(workspace.router)
app.include_router(payments.router)
app.include_router(logging.router)
app.include_router(admin.router)
app.include_router(scraping.router)

@app.get("/")
def get_root():
    return {
        "status": "online",
        "service": "Counsly Advisory Engine",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
    )
