from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas import ParseRun, ParsedAd
from app import storage

router = APIRouter(prefix="/api/avito")

@router.get("/runs", response_model=List[ParseRun])
async def list_runs():
    return storage.list_runs()

@router.get("/runs/{run_id}", response_model=ParseRun)
async def get_run(run_id: str):
    run = storage.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.get("/parsed-ads", response_model=List[ParsedAd])
async def list_parsed_ads(run_id: str = None):
    ads = storage.list_parsed_ads()
    if run_id:
        ads = [ad for ad in ads if ad.run_id == run_id]
    return ads

@router.get("/parsed-ads/{ad_id}", response_model=ParsedAd)
async def get_parsed_ad(ad_id: str):
    ad = storage.get_parsed_ad(ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Parsed Ad not found")
    return ad
