from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.ask import router as ask_router
from app.api.chat import router as chat_router
from app.api.eligibility import router as eligibility_router
from app.api.upc import router as upc_router
from app.config import get_settings
from app.db import init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(upc_router)
app.include_router(eligibility_router)
app.include_router(ask_router)
app.include_router(chat_router)


@app.get('/', response_class=HTMLResponse)
async def index() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>Keepa Scout</title>
      </head>
      <body>
        <h1>Keepa Scout</h1>
        <p>Service is running.</p>
        <ul>
          <li><a href="/health">GET /health</a></li>
          <li><a href="/upc?upc=70537500052">GET /upc</a></li>
          <li><a href="/eligibility/B00HEON30Y">GET /eligibility/{asin}</a></li>
        </ul>
        <p>POST endpoints: <code>/eligibility/batch</code>, <code>/ask</code>, <code>/chat</code></p>
      </body>
    </html>
    """


@app.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok'}
