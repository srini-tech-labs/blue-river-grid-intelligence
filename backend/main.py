"""Blue River Grid Intelligence — FastAPI entrypoint.

Serves the /api/* routes and the prebuilt React bundle from the same origin.
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME
from .errors import AppError
from .routers import ai, data, health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("blue_river")

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title=APP_NAME, docs_url=None, redoc_url=None, openapi_url=None)


@app.exception_handler(AppError)
async def _app_error(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(RequestValidationError)
async def _validation_error(_: Request, exc: RequestValidationError):
    problems = []
    for e in exc.errors():
        field = ".".join(str(p) for p in e.get("loc", ()) if p not in ("body", "query", "path"))
        problems.append(f"{field}: {e.get('msg')}" if field else str(e.get("msg")))
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "INVALID_REQUEST", "message": "; ".join(problems) or "Invalid request."}},
    )


@app.exception_handler(Exception)
async def _unhandled(_: Request, exc: Exception):
    log.exception("unhandled error")
    return JSONResponse(status_code=500, content=AppError().to_dict())


app.include_router(health.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.api_route("/api/{rest:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
async def _api_not_found(rest: str):
    return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "Unknown API route."}})


if (STATIC_DIR / "_app").is_dir():
    app.mount("/_app", StaticFiles(directory=STATIC_DIR / "_app"), name="bundle")


@app.get("/{full_path:path}", include_in_schema=False)
async def _spa(full_path: str):
    # Serve real top-level files (favicon etc.), otherwise index.html for client-side routes.
    candidate = (STATIC_DIR / full_path).resolve()
    if full_path and candidate.is_file() and STATIC_DIR.resolve() in candidate.parents:
        return FileResponse(candidate)
    index = STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
    return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "UI bundle not built."}})
