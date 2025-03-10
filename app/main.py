import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api import router as api_router
from core.settings import settings
from core.models.db_helper import db_helper


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    db_helper.dispose()


app = FastAPI(
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    title="API Avito shop",
    version="1.0.0"
)

app.include_router(
    api_router,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host = settings.run.host,
        port = settings.run.port
    )