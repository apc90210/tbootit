import pytest
from app.routers.integrations import is_safe_remote_url

def test_remote_photo_ssrf_block_private_and_local_urls():
    """Verify is_safe_remote_url blocks localhost, private IPs, link-local, file://, ftp://."""
    assert not is_safe_remote_url("http://localhost/image.jpg")
    assert not is_safe_remote_url("http://127.0.0.1/image.jpg")
    assert not is_safe_remote_url("http://10.0.0.5/image.jpg")
    assert not is_safe_remote_url("http://192.168.1.1/image.jpg")
    assert not is_safe_remote_url("http://172.16.0.1/image.jpg")
    assert not is_safe_remote_url("http://169.254.169.254/latest/meta-data")
    assert not is_safe_remote_url("file:///etc/passwd")
    assert not is_safe_remote_url("ftp://example.com/file.jpg")
    assert not is_safe_remote_url("http://[::1]/image.jpg")

    # Safe public URLs
    assert is_safe_remote_url("https://10.img.avito.st/image/1/1.xyz")
    assert is_safe_remote_url("https://cdn.example.com/photo.png")
