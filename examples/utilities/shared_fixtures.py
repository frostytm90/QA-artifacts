"""
Shared Pytest Fixtures.

This demonstrates the reusable fixture patterns I created
for consistent test setup across multiple test suites.
"""

import pytest
import os
from typing import Generator, Any
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class TestConfig:
    """Test configuration container."""
    base_url: str
    api_version: str
    timeout: int
    headless: bool
    environment: str


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """
    Session-scoped configuration fixture.

    Loads configuration from environment variables
    with sensible defaults for local development.
    """
    return TestConfig(
        base_url=os.getenv("BASE_URL", "http://localhost:8080"),
        api_version=os.getenv("API_VERSION", "v1"),
        timeout=int(os.getenv("TIMEOUT", "30")),
        headless=os.getenv("HEADLESS", "true").lower() == "true",
        environment=os.getenv("ENVIRONMENT", "local")
    )


@pytest.fixture(scope="session")
def api_url(test_config: TestConfig) -> str:
    """Construct full API URL."""
    return f"{test_config.base_url}/api/{test_config.api_version}"


# --- Database Fixtures ---

@pytest.fixture(scope="function")
def db_connection(test_config: TestConfig) -> Generator:
    """
    Database connection fixture with automatic cleanup.

    Creates a fresh connection for each test and
    rolls back any changes after the test completes.
    """
    # This is a simplified example - actual implementation
    # would use your database library
    class MockConnection:
        def __init__(self):
            self.in_transaction = False

        def begin(self):
            self.in_transaction = True

        def rollback(self):
            self.in_transaction = False

        def commit(self):
            self.in_transaction = False

        def execute(self, query: str):
            pass

    connection = MockConnection()
    connection.begin()

    yield connection

    # Rollback any uncommitted changes
    if connection.in_transaction:
        connection.rollback()


@pytest.fixture
def clean_db(db_connection) -> Generator:
    """
    Fixture that ensures clean database state.

    Truncates test tables before and after each test.
    """
    tables_to_clean = ["test_users", "test_orders", "test_products"]

    def truncate_tables():
        for table in tables_to_clean:
            db_connection.execute(f"TRUNCATE TABLE {table} CASCADE")

    truncate_tables()
    yield db_connection
    truncate_tables()


# --- Resource Management Fixtures ---

class ResourceTracker:
    """Track resources created during tests for cleanup."""

    def __init__(self):
        self._resources: list[tuple[str, Any]] = []

    def track(self, resource_type: str, resource_id: Any) -> None:
        """Register a resource for cleanup."""
        self._resources.append((resource_type, resource_id))

    def cleanup(self, cleanup_func) -> None:
        """Clean up all tracked resources."""
        for resource_type, resource_id in reversed(self._resources):
            try:
                cleanup_func(resource_type, resource_id)
            except Exception as e:
                print(f"Failed to cleanup {resource_type}/{resource_id}: {e}")
        self._resources.clear()


@pytest.fixture
def resource_tracker() -> Generator[ResourceTracker, None, None]:
    """
    Fixture for tracking and cleaning up test resources.

    Usage:
        def test_something(resource_tracker, api_client):
            user = api_client.create_user(...)
            resource_tracker.track("user", user.id)
            # User will be deleted after test
    """
    tracker = ResourceTracker()
    yield tracker

    # Cleanup function - customize based on your needs
    def cleanup(resource_type: str, resource_id: Any):
        print(f"Cleaning up {resource_type}: {resource_id}")
        # Add actual cleanup logic here

    tracker.cleanup(cleanup)


# --- Time-related Fixtures ---

@pytest.fixture
def freeze_time():
    """
    Context manager fixture for freezing time in tests.

    Usage:
        def test_time_sensitive(freeze_time):
            with freeze_time("2024-01-15 10:00:00"):
                result = get_current_timestamp()
                assert result == expected_timestamp
    """
    @contextmanager
    def _freeze(timestamp: str):
        # In real implementation, use freezegun or similar
        # This is a simplified example
        import datetime
        original_now = datetime.datetime.now

        frozen_time = datetime.datetime.fromisoformat(timestamp)
        datetime.datetime.now = lambda: frozen_time

        try:
            yield frozen_time
        finally:
            datetime.datetime.now = original_now

    return _freeze


# --- Retry and Wait Fixtures ---

@pytest.fixture
def wait_for():
    """
    Fixture for waiting with polling.

    Usage:
        def test_async_operation(wait_for):
            result = wait_for(
                lambda: api.get_status() == "complete",
                timeout=30,
                interval=1
            )
    """
    import time

    def _wait_for(
        condition,
        timeout: int = 30,
        interval: float = 0.5,
        message: str = "Condition not met"
    ) -> bool:
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                if condition():
                    return True
            except Exception:
                pass
            time.sleep(interval)

        raise TimeoutError(f"{message} within {timeout} seconds")

    return _wait_for


# --- Markers and Skip Conditions ---

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "smoke: mark test as smoke test")
    config.addinivalue_line("markers", "regression: mark test as regression test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "flaky: mark test as potentially flaky")


@pytest.fixture(autouse=True)
def skip_in_ci(request):
    """Skip tests marked with 'skip_ci' when running in CI."""
    if request.node.get_closest_marker("skip_ci"):
        if os.getenv("CI"):
            pytest.skip("Skipped in CI environment")


# --- Logging and Debugging ---

@pytest.fixture(autouse=True)
def test_logger(request):
    """Fixture that logs test start/end for debugging."""
    test_name = request.node.name

    print(f"\n{'='*60}")
    print(f"STARTING: {test_name}")
    print(f"{'='*60}")

    yield

    print(f"\n{'='*60}")
    print(f"FINISHED: {test_name}")
    print(f"{'='*60}")
