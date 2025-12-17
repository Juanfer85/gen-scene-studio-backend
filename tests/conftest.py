"""
Pytest configuration and shared fixtures for Gen Scene Studio backend tests.

This file contains global fixtures, configuration, and utilities
used across all test categories.
"""

import os
import sys
import pytest
import tempfile
import asyncio
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.config import settings
from repositories.connection_manager import DatabaseManager
from repositories.job import JobRepository
from repositories.render import RenderRepository
from repositories.assets_cache import AssetsCacheRepository
from models.entities import Job, JobState, Render, RenderStatus, RenderQuality, AssetsCache
from migrations.manager import MigrationManager
from migrations.versions import MIGRATIONS


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_client():
    """Create a test async HTTP client."""
    import httpx
    async with httpx.AsyncClient(app=None, base_url="http://test") as client:
        yield client


@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
        yield temp_file.name
    # Cleanup is handled by tempfile context manager


@pytest.fixture
def test_db_path(temp_database) -> str:
    """Get temporary database path."""
    return temp_database


@pytest.fixture
def job_repository(test_db_path) -> JobRepository:
    """Create JobRepository instance with test database."""
    repo = JobRepository(test_db_path)
    repo.create_table()
    return repo


@pytest.fixture
def render_repository(test_db_path) -> RenderRepository:
    """Create RenderRepository instance with test database."""
    repo = RenderRepository(test_db_path)
    repo.create_table()
    return repo


@pytest.fixture
def assets_cache_repository(test_db_path) -> AssetsCacheRepository:
    """Create AssetsCacheRepository instance with test database."""
    repo = AssetsCacheRepository(test_db_path)
    repo.create_table()
    return repo


@pytest.fixture
def database_manager(test_db_path) -> DatabaseManager:
    """Create DatabaseManager instance with test database."""
    manager = DatabaseManager(test_db_path)
    manager.initialize_database()
    yield manager
    manager.close()


@pytest.fixture
def migration_manager(test_db_path) -> MigrationManager:
    """Create MigrationManager instance with test database."""
    return MigrationManager(test_db_path)


@pytest.fixture
def sample_job() -> Job:
    """Sample job entity for testing."""
    return Job(
        job_id="test-job-123",
        state=JobState.QUEUED,
        progress=0,
        created_at=1234567890,
        updated_at=1234567890
    )


@pytest.fixture
def sample_completed_job() -> Job:
    """Sample completed job entity for testing."""
    return Job(
        job_id="test-job-completed",
        state=JobState.COMPLETED,
        progress=100,
        created_at=1234567890,
        updated_at=1234567900
    )


@pytest.fixture
def sample_render() -> Render:
    """Sample render entity for testing."""
    return Render(
        job_id="test-job-123",
        item_id="render-001",
        hash="abc123def456",
        quality=RenderQuality.HIGH,
        url="http://example.com/render.mp4",
        status=RenderStatus.COMPLETED,
        created_at=1234567890,
        updated_at=1234567900
    )


@pytest.fixture
def sample_assets_cache() -> AssetsCache:
    """Sample assets cache entity for testing."""
    return AssetsCache(
        hash="abc123def456",
        url="http://example.com/asset.mp4",
        created_at=1234567890
    )


@pytest.fixture
def multiple_jobs() -> list[Job]:
    """Multiple sample jobs for testing."""
    return [
        Job(job_id="job-1", state=JobState.QUEUED, progress=0, created_at=1234567890),
        Job(job_id="job-2", state=JobState.PROCESSING, progress=50, created_at=1234567891),
        Job(job_id="job-3", state=JobState.COMPLETED, progress=100, created_at=1234567892),
        Job(job_id="job-4", state=JobState.ERROR, progress=25, created_at=1234567893),
    ]


@pytest.fixture
def multiple_renders() -> list[Render]:
    """Multiple sample renders for testing."""
    return [
        Render(
            job_id="job-1", item_id="render-1", hash="hash1",
            quality=RenderQuality.LOW, status=RenderStatus.COMPLETED
        ),
        Render(
            job_id="job-1", item_id="render-2", hash="hash2",
            quality=RenderQuality.MEDIUM, status=RenderStatus.PROCESSING
        ),
        Render(
            job_id="job-2", item_id="render-1", hash="hash3",
            quality=RenderQuality.HIGH, status=RenderStatus.PENDING
        ),
    ]


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    original_settings = {}

    # Override settings for testing
    settings.DATABASE_URL = "sqlite:///test.db"
    settings.BACKEND_API_KEY = "test-api-key"
    settings.MEDIA_DIR = "/tmp/test_media"

    yield settings

    # Restore original settings
    for key, value in original_settings.items():
        setattr(settings, key, value)


@pytest.fixture
def fastapi_app():
    """Create FastAPI app instance for testing."""
    from main_refactored import app
    return app


@pytest.fixture
async def test_client(fastapi_app):
    """Create test client for FastAPI app."""
    from httpx import AsyncClient
    async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls."""
    with pytest.MonkeyPatch() as m:
        m.setattr("subprocess.run", Mock(return_value=Mock(returncode=0, stdout="ffmpeg version 4.4")))
        yield m


@pytest.fixture
def mock_time():
    """Mock time functions for deterministic tests."""
    import time
    with pytest.MonkeyPatch() as m:
        m.setattr(time.time, lambda: 1234567890)
        m.setattr(time.sleep, AsyncMock())
        yield m


@pytest.fixture
def temp_media_dir():
    """Create temporary media directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def mock_uuid():
    """Mock UUID generation for predictable tests."""
    import uuid
    with pytest.MonkeyPatch() as m:
        m.setattr(uuid.uuid4, lambda: Mock(hex="test-uuid-123"))
        yield m


# Custom markers for test categorization
pytest_plugins = ["pytest_asyncio", "pytest_mock"]

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, realistic)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (slowest, full stack)"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and load tests"
    )
    config.addinivalue_line(
        "markers", "slow: Mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: Tests requiring database"
    )
    config.addinivalue_line(
        "markers", "api: Tests requiring HTTP API"
    )
    config.addinivalue_line(
        "markers", "migration: Migration system tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on file path
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance/" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

        # Add markers based on test content
        if "database" in str(item.fspath):
            item.add_marker(pytest.mark.database)
        if "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        if "migration" in str(item.fspath):
            item.add_marker(pytest.mark.migration)


# Test utilities
class TestDatabase:
    """Utility class for database test operations."""

    @staticmethod
    def setup_test_tables(db_path: str) -> None:
        """Set up all test tables."""
        job_repo = JobRepository(db_path)
        render_repo = RenderRepository(db_path)
        assets_repo = AssetsCacheRepository(db_path)

        job_repo.create_table()
        render_repo.create_table()
        assets_repo.create_table()

    @staticmethod
    def cleanup_database(db_path: str) -> None:
        """Clean up test database."""
        try:
            os.remove(db_path)
        except FileNotFoundError:
            pass


class TestAssertions:
    """Custom assertion helpers for tests."""

    @staticmethod
    def assert_job_equal(actual: Job, expected: Job, msg: str = None) -> None:
        """Assert two jobs are equal with helpful error message."""
        assert actual.job_id == expected.job_id, msg or f"Job ID mismatch: {actual.job_id} != {expected.job_id}"
        assert actual.state == expected.state, msg or f"Job state mismatch: {actual.state} != {expected.state}"
        assert actual.progress == expected.progress, msg or f"Job progress mismatch: {actual.progress} != {expected.progress}"

    @staticmethod
    def assert_render_equal(actual: Render, expected: Render, msg: str = None) -> None:
        """Assert two renders are equal with helpful error message."""
        assert actual.job_id == expected.job_id, msg or f"Render job_id mismatch"
        assert actual.item_id == expected.item_id, msg or f"Render item_id mismatch"
        assert actual.quality == expected.quality, msg or f"Render quality mismatch"
        assert actual.status == expected.status, msg or f"Render status mismatch"


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_job(job_id: str = None, state: JobState = JobState.QUEUED,
                   progress: int = 0) -> Job:
        """Create a test job with default values."""
        return Job(
            job_id=job_id or f"test-job-{os.urandom(4).hex()}",
            state=state,
            progress=progress,
            created_at=1234567890
        )

    @staticmethod
    def create_render(job_id: str = "test-job", item_id: str = "render-001",
                     quality: RenderQuality = RenderQuality.HIGH,
                     status: RenderStatus = RenderStatus.PENDING) -> Render:
        """Create a test render with default values."""
        return Render(
            job_id=job_id,
            item_id=item_id,
            hash=f"hash-{os.urandom(4).hex()}",
            quality=quality,
            url=None,
            status=status,
            created_at=1234567890
        )

    @staticmethod
    def create_assets_cache(hash_value: str = None) -> AssetsCache:
        """Create a test assets cache with default values."""
        return AssetsCache(
            hash=hash_value or f"hash-{os.urandom(4).hex()}",
            url=f"http://example.com/asset-{os.urandom(4).hex()}.mp4",
            created_at=1234567890
        )


# Performance testing utilities
class PerformanceTestHelper:
    """Helper for performance testing."""

    @staticmethod
    async def measure_async_time(func, *args, **kwargs) -> tuple:
        """Measure execution time of async function."""
        import time
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time

    @staticmethod
    def measure_time(func, *args, **kwargs) -> tuple:
        """Measure execution time of sync function."""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time


# Async test helpers
class AsyncTestHelper:
    """Helper for async testing operations."""

    @staticmethod
    async def gather_with_timeout(*tasks, timeout: float = 5.0):
        """Run tasks with timeout."""
        try:
            return await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tasks did not complete within {timeout} seconds")

    @staticmethod
    async def wait_for_condition(condition_func, timeout: float = 5.0, check_interval: float = 0.1):
        """Wait for a condition to become true."""
        start_time = asyncio.get_event_loop().time()
        while True:
            if condition_func():
                return True

            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                raise TimeoutError("Condition not met within timeout")

            await asyncio.sleep(check_interval)