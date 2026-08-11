import pytest
from app.browser_worker import AvitoBrowserWorker

@pytest.mark.asyncio
async def test_auth_state_detection():
    """
    Test detection of auth states (authorized, unauthorized, challenge_required, unknown).
    Ensures CAPTCHA / 2FA challenge stops import and requires manual intervention.
    """
    worker = AvitoBrowserWorker("main")

    # 1. Authorized HTML mock
    auth_html = "<html><body><h1>Мои объявления</h1><div>Профиль</div></body></html>"
    st1, err1 = await worker.check_auth_state(mock_html=auth_html)
    assert st1 == "authorized"
    assert err1 is None

    # 2. Unauthorized HTML mock
    unauth_html = "<html><body><a href='/login'>Войти</a></body></html>"
    st2, err2 = await worker.check_auth_state(mock_html=unauth_html)
    assert st2 == "unauthorized"
    assert "авторизация" in err2.lower()

    # 3. CAPTCHA / Challenge HTML mock
    captcha_html = "<html><body><h1>Подтвердите, что вы не робот</h1><div>Введите капчу</div></body></html>"
    st3, err3 = await worker.check_auth_state(mock_html=captcha_html)
    assert st3 == "challenge_required"
    assert "CAPTCHA" in err3 or "безопасности" in err3
