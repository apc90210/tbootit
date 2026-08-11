import pytest
from app.main import rewrite_location_header

def test_proxy_location_rewrite_cases():
    """Verify various location header rewriting scenarios for backend port isolation."""
    # Absolute URL with internal port -> strip origin, keep path
    assert rewrite_location_header("http://localhost:8040/repairs/repairs/12", "/repairs") == "/repairs/repairs/12"
    assert rewrite_location_header("http://repairs-module:8040/repairs/repairs/12", "/repairs") == "/repairs/repairs/12"
    assert rewrite_location_header("http://inventory-sales-module:8030/products", "/inventory") == "/inventory/products"
    
    # Relative path without prefix -> add prefix
    assert rewrite_location_header("/products", "/inventory") == "/inventory/products"
    assert rewrite_location_header("/repairs", "/repairs") == "/repairs"
    
    # Relative path already prefixed -> do not double prefix
    assert rewrite_location_header("/inventory/products", "/inventory") == "/inventory/products"
    assert rewrite_location_header("/repairs/repairs", "/repairs") == "/repairs/repairs"
    assert rewrite_location_header("/avito/accounts", "/avito") == "/avito/accounts"
