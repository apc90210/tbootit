import os
import uuid
from app.schemas import ParseRun, ParsedAd
from app import storage

def test_storage_run():
    run_id = str(uuid.uuid4())
    run = ParseRun(run_id=run_id, profile_url="http://test", status="created", started_at="now")
    storage.save_run(run)
    
    loaded = storage.get_run(run_id)
    assert loaded is not None
    assert loaded.run_id == run_id
    assert loaded.status == "created"

def test_storage_ad():
    ad = ParsedAd(
        id=str(uuid.uuid4()),
        run_id="run",
        source_url="http",
        title="Test",
        parse_status="parsed",
        created_at="now"
    )
    storage.save_parsed_ad(ad)
    
    loaded = storage.get_parsed_ad(ad.id)
    assert loaded is not None
    assert loaded.title == "Test"
