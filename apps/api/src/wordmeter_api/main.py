from fastapi import FastAPI

from wordmeter_api.routers import analyze, auth

app = FastAPI(title="Wordmeter API", version="0.1.0")
app.include_router(auth.router)
app.include_router(analyze.router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
