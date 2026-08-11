import os
import pytest
from app.browser_worker import AvitoBrowserWorker

def test_browser_profile_storage_dir_construction():
    """
    Test persistent user-data-dir path construction for an owner-created profile.
    """
    worker = AvitoBrowserWorker("acc_test_uuid_123")
    assert "acc_test_uuid_123" in worker.profile_dir
    assert os.path.exists(worker.profile_dir)

def test_captcha_and_challenge_detection():
    """
    Test that CAPTCHA and anti-bot challenge signatures trigger challenge_required status.
    """
    worker = AvitoBrowserWorker("acc_test_uuid_123")

    captcha_html = "<html><body><h1>Подтвердите, что вы не робот</h1><div>Введите капчу</div></body></html>"
    assert worker.detect_challenge_or_captcha(captcha_html) is True

    normal_html = "<html><body><h1>Мои объявления</h1></body></html>"
    assert worker.detect_challenge_or_captcha(normal_html) is False
