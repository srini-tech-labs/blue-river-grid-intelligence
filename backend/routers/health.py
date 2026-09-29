from fastapi import APIRouter

from ..config import APP_NAME

router = APIRouter()


@router.get("/health")
def health():
    # Deliberately makes no warehouse, search, or model calls.
    return {"status": "ok", "app": APP_NAME, "synthetic_environment": True}
