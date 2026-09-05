from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.exception_handlers import register_exception_handlers
from app.api.v1.router import api_v1_router
from app.core.logging import configure_logging

configure_logging()

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://localhost",
    "capacitor://localhost",
    "https://eduradar.4one.ovh",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/test")
async def root():
    return {"message": "Backend FastAPI"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0")
