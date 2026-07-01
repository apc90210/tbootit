import os
import json
from typing import List, Optional
from app.config import settings
from app.schemas import ParseRun, ParsedAd

def _get_runs_dir() -> str:
    path = os.path.join(settings.AVITO_STORAGE_DIR, "runs")
    os.makedirs(path, exist_ok=True)
    return path

def _get_run_dir(run_id: str) -> str:
    path = os.path.join(_get_runs_dir(), run_id)
    os.makedirs(path, exist_ok=True)
    return path

def _get_ads_dir() -> str:
    path = os.path.join(settings.AVITO_STORAGE_DIR, "ads")
    os.makedirs(path, exist_ok=True)
    return path

def save_run(run: ParseRun):
    run_dir = _get_run_dir(run.run_id)
    with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as f:
        f.write(run.model_dump_json(indent=2))

def get_run(run_id: str) -> Optional[ParseRun]:
    path = os.path.join(_get_run_dir(run_id), "run.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return ParseRun(**json.load(f))

def list_runs() -> List[ParseRun]:
    runs = []
    runs_dir = _get_runs_dir()
    for run_id in os.listdir(runs_dir):
        run = get_run(run_id)
        if run:
            runs.append(run)
    return sorted(runs, key=lambda x: x.started_at, reverse=True)

def save_html_snapshot(run_id: str, filename: str, html: str):
    run_dir = _get_run_dir(run_id)
    path = os.path.join(run_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

def save_parsed_ad(ad: ParsedAd):
    ads_dir = _get_ads_dir()
    path = os.path.join(ads_dir, f"{ad.id}.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(ad.model_dump_json(indent=2))

def get_parsed_ad(ad_id: str) -> Optional[ParsedAd]:
    ads_dir = _get_ads_dir()
    path = os.path.join(ads_dir, f"{ad_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return ParsedAd(**json.load(f))

def list_parsed_ads() -> List[ParsedAd]:
    ads = []
    ads_dir = _get_ads_dir()
    for filename in os.listdir(ads_dir):
        if filename.endswith(".json"):
            ad_id = filename[:-5]
            ad = get_parsed_ad(ad_id)
            if ad:
                ads.append(ad)
    return sorted(ads, key=lambda x: x.created_at, reverse=True)
