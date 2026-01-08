import pytest
import os
from faker import Faker


@pytest.fixture(scope="session")
def faker():
    return Faker()


@pytest.fixture(scope="session")
def api_base_url():
    return os.getenv("API_BASE_URL", "http://localhost:8080/api/v1")


@pytest.fixture(scope="session")
def test_creds():
    """
    Load test credentials from environment variables.
    Set these in your .env file or CI/CD pipeline.
    """
    return {
        "email": os.getenv("TEST_USER_EMAIL"),
        "password": os.getenv("TEST_USER_PASSWORD")
    }


@pytest.fixture(autouse=True)
def log_test(request):
    print(f"\n>>> {request.node.name}")
    yield
    print(f"<<< {request.node.name}")


@pytest.fixture
def assert_fast():
    """check response time is acceptable"""
    def _check(resp, max_ms=1000):
        assert resp.elapsed_ms < max_ms, f"too slow: {resp.elapsed_ms}ms"
    return _check
