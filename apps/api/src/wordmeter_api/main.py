import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from wordmeter_api.config import settings
from wordmeter_api.routers import analyze, auth, live, stats, transcribe
from wordmeter_api.speech.transcriber import warm_up


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.preload_models:
        await asyncio.to_thread(warm_up)
    yield


app = FastAPI(title="Wordmeter API", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(stats.router)
app.include_router(transcribe.router)
app.include_router(live.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
