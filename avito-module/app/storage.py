import os
import json
from typing import List, Optional, Dict, Any
from app.config import settings
from app.schemas import ParseRun, ParsedAd, AvitoAccountProfile, ImportRun

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
        if filename.endswith(".json") and not filename.endswith("_import.json"):
            ad_id = filename[:-5]
            ad = get_parsed_ad(ad_id)
            if ad:
                ads.append(ad)
    return sorted(ads, key=lambda x: x.created_at, reverse=True)

def save_import_status(ad_id: str, status_data: Dict[str, Any]):
    ads_dir = _get_ads_dir()
    path = os.path.join(ads_dir, f"{ad_id}_import.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)

def get_import_status(ad_id: str) -> Optional[Dict[str, Any]]:
    ads_dir = _get_ads_dir()
    path = os.path.join(ads_dir, f"{ad_id}_import.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# Stage 06A Account Profiles & Import Runs Storage
def _get_profiles_file() -> str:
    os.makedirs(settings.AVITO_STORAGE_DIR, exist_ok=True)
    return os.path.join(settings.AVITO_STORAGE_DIR, "profiles.json")

def list_profiles() -> List[AvitoAccountProfile]:
    path = _get_profiles_file()
    if not os.path.exists(path):
        defaults = [
            AvitoAccountProfile(account_key="main", display_name="Avito — Основной"),
            AvitoAccountProfile(account_key="laptops", display_name="Avito — Ноутбуки"),
            AvitoAccountProfile(account_key="office", display_name="Avito — Оргтехника")
        ]
        save_profiles(defaults)
        return defaults
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [AvitoAccountProfile(**p) for p in data]

def save_profiles(profiles: List[AvitoAccountProfile]):
    path = _get_profiles_file()
    with open(path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in profiles], f, ensure_ascii=False, indent=2)

def get_profile(account_key: str) -> Optional[AvitoAccountProfile]:
    profiles = list_profiles()
    for p in profiles:
        if p.account_key == account_key:
            return p
    return None

def save_profile(profile: AvitoAccountProfile):
    profiles = list_profiles()
    updated = False
    for idx, p in enumerate(profiles):
        if p.account_key == profile.account_key:
            profiles[idx] = profile
            updated = True
            break
    if not updated:
        profiles.append(profile)
    save_profiles(profiles)

def delete_profile(account_key: str):
    profiles = list_profiles()
    profiles = [p for p in profiles if p.account_key != account_key]
    save_profiles(profiles)

def _get_import_runs_dir() -> str:
    path = os.path.join(settings.AVITO_STORAGE_DIR, "import_runs")
    os.makedirs(path, exist_ok=True)
    return path

def save_import_run(run: ImportRun):
    run_dir = _get_import_runs_dir()
    path = os.path.join(run_dir, f"{run.run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(run.model_dump_json(indent=2))

def get_import_run(run_id: str) -> Optional[ImportRun]:
    run_dir = _get_import_runs_dir()
    path = os.path.join(run_dir, f"{run_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return ImportRun(**json.load(f))

def list_import_runs() -> List[ImportRun]:
    runs = []
    run_dir = _get_import_runs_dir()
    if os.path.exists(run_dir):
        for filename in os.listdir(run_dir):
            if filename.endswith(".json"):
                run_id = filename[:-5]
                run = get_import_run(run_id)
                if run:
                    runs.append(run)
    return sorted(runs, key=lambda x: x.started_at, reverse=True)
