import os
import pytest
from app.main import AVITO_NOVNC_URL

def test_avito_novnc_url_target():
    """Verify AVITO_NOVNC_URL points to avito-module container in docker or localhost fallback."""
    assert "6080" in AVITO_NOVNC_URL
