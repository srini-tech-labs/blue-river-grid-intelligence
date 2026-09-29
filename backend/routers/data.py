"""Deterministic Delta-backed routes. No LLM involvement."""

from fastapi import APIRouter, Query

from ..services import assets, reliability

router = APIRouter()


@router.get("/reliability")
def get_reliability():
    return reliability.get_reliability_summary()


@router.get("/operations/summary")
def get_operations_summary():
    return reliability.get_operations_summary()


@router.get("/assets")
def list_priority_assets(limit: int = Query(default=10, ge=1, le=assets.MAX_LIMIT)):
    return assets.get_high_risk_assets(limit)


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str):
    return assets.get_asset_360(asset_id.strip().upper())


@router.get("/assets/{asset_id}/timeline")
def get_asset_timeline(asset_id: str):
    return assets.get_asset_timeline(asset_id.strip().upper())
