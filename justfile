alias cov := coverage
alias ta := testall

# Run unit tests with coverage generation
@test *FLAGS:
    uv run coverage run -m pytest -m "not feature_notification" {{FLAGS}}

# Run unit tests, including optional features with coverage generation
@testall:
    uv run coverage run -m pytest

# Generate coverage report
@coverage REPORT_TYPE='report':
    uv run coverage {{REPORT_TYPE}}

# Lint source
@lint:
    uv run --frozen ruff check src/
    uv run --frozen ty check src/

# Clean dist
@clean:
    echo "Cleaning up existing artifacts…"
    rm -f "dist/*.{tar.gz,whl}"

# Build dist
@build: clean
    echo "Building dist…"
    uv build

# Upgrade dependencies
@upgrade:
    echo "Upgrading dependencies…"
    uv lock --upgrade
