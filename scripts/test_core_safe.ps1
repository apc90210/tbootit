# Safe test runner for Core container
$ErrorActionPreference = "Stop"

Write-Output "Running isolated Core unit tests..."
docker compose run --rm -v "${PWD}/core/tests:/app/tests" -e DATABASE_URL=sqlite:////tmp/technoreboot_core_safe_tests.db core pytest

