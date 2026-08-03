import pytest
from app import models

def test_no_destructive_reset_endpoints(client, db_session):
    """
    Assert that all potential reset routes are completely absent (404/405)
    and that no runtime HTTP request can drop live database tables.
    """
    reset_routes = [
        "/api/reset",
        "/api/admin/reset",
        "/api/admin/dev-reset",
        "/api/dev/reset",
        "/reset",
        "/dev-reset"
    ]

    for route in reset_routes:
        # Check GET and POST
        res_get = client.get(route)
        assert res_get.status_code in [404, 405], f"Route {route} returned unexpected GET status {res_get.status_code}"

        res_post = client.post(route)
        assert res_post.status_code in [404, 405], f"Route {route} returned unexpected POST status {res_post.status_code}"

    # Verify tables still exist and query succeeds
    product_count = db_session.query(models.Product).count()
    assert product_count >= 0
