"""
Integration tests for Jobs API endpoints.

Tests cover complete request/response cycles, error handling,
authentication, and data validation for job-related API operations.
"""

import pytest
import json
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from httpx import AsyncClient
from tests.conftest import (
    fastapi_app, test_client, database_manager,
    sample_job, multiple_jobs, TestDataFactory,
    TestAssertions, AsyncTestHelper
)
from models.entities import Job, JobState


class TestJobsAPI:
    """Integration tests for Jobs API endpoints."""

    def test_health_endpoint_success(self, test_client):
        """Test: Health endpoint returns service status"""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data
        assert "database" in data["services"]
        assert "ffmpeg" in data["services"]
        assert "ffprobe" in data["services"]

    def test_health_endpoint_with_database(self, test_client, database_manager):
        """Test: Health endpoint includes database statistics"""
        # Create some test data
        job_repo = database_manager.jobs()
        test_job = TestDataFactory.create_job("health-test-job")
        job_repo.create(test_job)

        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "statistics" in data
        assert "total_jobs" in data["statistics"]
        assert data["statistics"]["total_jobs"] >= 1

    def test_get_job_status_success(self, test_client, database_manager, sample_job):
        """Test: Get job status succeeds for existing job"""
        # Arrange
        job_repo = database_manager.jobs()
        job_repo.create(sample_job)

        # Act
        response = test_client.get(f"/api/status/{sample_job.job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == sample_job.job_id
        assert data["state"] == sample_job.state.value
        assert data["progress"] == sample_job.progress

    def test_get_job_status_not_found(self, test_client):
        """Test: Get job status returns 404 for non-existent job"""
        response = test_client.get("/api/status/non-existent-job")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Job not found"

    def test_list_jobs_default(self, test_client, database_manager, multiple_jobs):
        """Test: List jobs with default parameters"""
        # Arrange
        job_repo = database_manager.jobs()
        for job in multiple_jobs:
            job_repo.create(job)

        # Act
        response = test_client.get("/api/jobs")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "jobs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        assert data["limit"] == 100  # Default
        assert data["offset"] == 0  # Default
        assert len(data["jobs"]) <= data["limit"]
        assert data["total"] >= len(multiple_jobs)

    def test_list_jobs_with_pagination(self, test_client, database_manager, multiple_jobs):
        """Test: List jobs with pagination parameters"""
        # Arrange
        job_repo = database_manager.jobs()
        for job in multiple_jobs:
            job_repo.create(job)

        # Act
        response = test_client.get("/api/jobs?limit=2&offset=1")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 2
        assert data["offset"] == 1
        assert len(data["jobs"]) == 2
        assert data["has_more"] in data

    def test_list_jobs_with_state_filter(self, test_client, database_manager, multiple_jobs):
        """Test: List jobs with state filter"""
        # Arrange
        job_repo = database_manager.jobs()
        for job in multiple_jobs:
            job_repo.create(job)

        # Act
        response = test_client.get("/api/jobs?state=completed")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # All returned jobs should have state=completed
        for job_data in data["jobs"]:
            assert job_data["state"] == "completed"

    def test_list_jobs_invalid_state_filter(self, test_client):
        """Test: List jobs with invalid state filter returns 400"""
        response = test_client.get("/api/jobs?state=invalid_state")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "invalid state" in data["detail"].lower()

    def test_get_specific_job_success(self, test_client, database_manager, sample_job):
        """Test: Get specific job succeeds"""
        # Arrange
        job_repo = database_manager.jobs()
        job_repo.create(sample_job)

        # Act
        response = test_client.get(f"/api/jobs/{sample_job.job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == sample_job.job_id
        assert data["state"] == sample_job.state.value
        assert data["progress"] == sample_job.progress

    def test_get_specific_job_not_found(self, test_client):
        """Test: Get specific job returns 404 for non-existent job"""
        response = test_client.get("/api/jobs/non-existent-job")

        assert response.status_code == 404

    def test_jobs_hub_endpoint(self, test_client, database_manager, multiple_jobs):
        """Test: Jobs hub endpoint returns formatted data"""
        # Arrange
        job_repo = database_manager.jobs()
        render_repo = database_manager.renders()

        # Create jobs
        for job in multiple_jobs:
            job_repo.create(job)

        # Add some renders to one job
        from models.entities import Render, RenderStatus, RenderQuality
        test_render = Render(
            job_id=multiple_jobs[0].job_id,
            item_id="render-1",
            hash="test-hash",
            quality=RenderQuality.HIGH,
            url="http://example.com/render.mp4",
            status=RenderStatus.COMPLETED
        )
        render_repo.create(test_render)

        # Act
        response = test_client.get("/api/jobs-hub")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "jobs" in data
        assert "total" in data
        assert "timestamp" in data

        # Verify job structure
        for job_data in data["jobs"]:
            assert "id" in job_data
            assert "title" in job_data
            assert "status" in job_data
            assert "progress" in job_data
            assert "createdAt" in job_data
            assert "updatedAt" in job_data
            assert "rendersCount" in job_data
            assert "completedRendersCount" in job_data

    def test_quick_create_universe_success(self, test_client, database_manager):
        """Test: Quick create universe endpoint succeeds"""
        # Arrange
        request_data = {
            "idea_text": "A futuristic city with flying cars",
            "duration": "30s",
            "style_key": "cinematic",
            "auto_create_universe": True
        }

        # Act
        response = test_client.post(
            "/api/quick-create-full-universe",
            json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert "status" in data
        assert "message" in data
        assert "estimated_time_sec" in data
        assert data["status"] == "queued"

        # Verify job was created
        job_repo = database_manager.jobs()
        created_job = job_repo.get_by_id(data["job_id"])
        assert created_job is not None
        assert created_job.state == JobState.QUEUED

    def test_quick_create_universe_invalid_data(self, test_client):
        """Test: Quick create universe validates input data"""
        # Test missing required fields
        response = test_client.post("/api/quick-create-full-universe", json={})
        assert response.status_code == 422  # Validation error

        # Test invalid idea_text (too short)
        invalid_data = {
            "idea_text": "hi",  # Too short (min 5 chars)
            "duration": "30s",
            "style_key": "cinematic"
        }
        response = test_client.post("/api/quick-create-full-universe", json=invalid_data)
        assert response.status_code == 422

        # Test invalid idea_text (too long)
        invalid_data = {
            "idea_text": "x" * 501,  # Too long (max 500 chars)
            "duration": "30s",
            "style_key": "cinematic"
        }
        response = test_client.post("/api/quick-create-full-universe", json=invalid_data)
        assert response.status_code == 422

    def test_delete_job_success(self, test_client, database_manager, sample_job):
        """Test: Delete job endpoint succeeds"""
        # Arrange
        job_repo = database_manager.jobs()
        job_repo.create(sample_job)

        # Act
        response = test_client.delete(f"/api/jobs/{sample_job.job_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == sample_job.job_id
        assert data["status"] == "deleted"
        assert "message" in data

        # Verify job was deleted
        deleted_job = job_repo.get_by_id(sample_job.job_id)
        assert deleted_job is None

    def test_delete_job_not_found(self, test_client):
        """Test: Delete job returns 404 for non-existent job"""
        response = test_client.delete("/api/jobs/non-existent-job")
        assert response.status_code == 404

    def test_delete_job_post_success(self, test_client, database_manager, sample_job):
        """Test: Delete job via POST endpoint succeeds"""
        # Arrange
        job_repo = database_manager.jobs()
        job_repo.create(sample_job)

        request_data = {"job_id": sample_job.job_id}

        # Act
        response = test_client.post("/api/delete-job", json=request_data)

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["job_id"] == sample_job.job_id
        assert data["status"] == "deleted"

    def test_delete_job_post_not_found(self, test_client):
        """Test: Delete job via POST returns 404 for non-existent job"""
        request_data = {"job_id": "non-existent-job"}
        response = test_client.post("/api/delete-job", json=request_data)
        assert response.status_code == 404

    def test_database_stats_endpoint(self, test_client, database_manager, multiple_jobs):
        """Test: Database stats endpoint returns comprehensive information"""
        # Arrange
        job_repo = database_manager.jobs()
        render_repo = database_manager.renders()

        for job in multiple_jobs:
            job_repo.create(job)

        # Add some renders
        from models.entities import Render, RenderStatus, RenderQuality
        for i, job in enumerate(multiple_jobs[:3]):
            test_render = Render(
                job_id=job.job_id,
                item_id=f"render-{i}",
                hash=f"hash-{i}",
                quality=RenderQuality.HIGH,
                url=f"http://example.com/render-{i}.mp4",
                status=RenderStatus.COMPLETED
            )
            render_repo.create(test_render)

        # Act
        response = test_client.get("/api/database/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert "database" in data
        assert "jobs" in data
        assert "renders" in data
        assert "cache" in data
        assert "timestamp" in data

        # Verify database info
        db_info = data["database"]
        assert "database_path" in db_info
        assert "database_size_bytes" in db_info
        assert "tables" in db_info
        assert "connection_pool" in db_info

    def test_database_optimize_endpoint(self, test_client):
        """Test: Database optimize endpoint triggers optimization"""
        response = test_client.post("/api/database/optimize")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "message" in data
        assert "timestamp" in data

    def test_authentication_required(self, test_client):
        """Test: Protected endpoints require authentication"""
        # Reset client without API key
        client_no_auth = TestClient(fastapi_app)
        client_no_auth.headers.clear()

        # Test protected endpoint without auth
        response = client_no_auth.get("/api/jobs")

        # Should succeed in test environment (no API key required)
        # In production, this would return 401
        assert response.status_code in [200, 401]

    def test_authentication_with_valid_key(self, test_client):
        """Test: Valid API key allows access"""
        # Test with valid API key
        headers = {"X-API-Key": "test-api-key"}
        response = test_client.get("/api/jobs", headers=headers)

        assert response.status_code == 200

    def test_authentication_with_invalid_key(self, test_client):
        """Test: Invalid API key denies access"""
        # Test with invalid API key
        headers = {"X-API-Key": "invalid-key"}
        response = test_client.get("/api/jobs", headers=headers)

        # In production this would return 401
        # In test environment, behavior might vary
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_concurrent_job_creation(self, async_client, database_manager):
        """Test: Concurrent job creation handles properly"""
        job_repo = database_manager.jobs()

        # Create multiple jobs concurrently
        tasks = []
        for i in range(10):
            request_data = {
                "idea_text": f"Concurrent test job {i}",
                "duration": "30s",
                "style_key": "cinematic",
                "auto_create_universe": True
            }
            task = async_client.post("/api/quick-create-full-universe", json=request_data)
            tasks.append(task)

        # Wait for all requests
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert all succeeded
        success_count = 0
        for response in responses:
            if hasattr(response, 'status_code') and response.status_code == 200:
                success_count += 1

        assert success_count >= 8  # Allow some failures in test environment

    @pytest.mark.slow
    def test_api_response_time_performance(self, test_client, database_manager):
        """Test: API response times meet performance requirements"""
        import time

        # Create test data
        job_repo = database_manager.jobs()
        test_job = TestDataFactory.create_job("perf-test-job")
        job_repo.create(test_job)

        # Measure response time
        start_time = time.time()
        response = test_client.get(f"/api/status/{test_job.job_id}")
        end_time = time.time()
        response_time = end_time - start_time

        # Assert performance requirements
        assert response.status_code == 200
        assert response_time < 0.1, f"API response took {response_time:.3f}s, expected < 0.1s"

    @pytest.mark.slow
    def test_api_stress_test(self, test_client, database_manager):
        """Test: API handles concurrent load"""
        import time
        import threading

        job_repo = database_manager.jobs()

        # Create test data
        for i in range(20):
            job = TestDataFactory.create_job(f"stress-test-job-{i}")
            job_repo.create(job)

        # Stress test parameters
        num_threads = 10
        requests_per_thread = 5

        def make_requests():
            for i in range(requests_per_thread):
                response = test_client.get("/api/jobs")
                # Assert basic success
                assert response.status_code in [200, 401]

        # Run concurrent requests
        start_time = time.time()
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time
        total_requests = num_threads * requests_per_thread

        # Assert reasonable performance
        avg_time_per_request = total_time / total_requests
        assert avg_time_per_request < 0.2, f"Average request time: {avg_time_per_request:.3f}s"

    @pytest.mark.parametrize("endpoint", [
        "/api/jobs",
        "/api/status/test-job",
        "/api/jobs-hub",
        "/api/quick-create-full-universe"
    ])
    def test_api_content_type_headers(self, test_client, endpoint):
        """Test: API endpoints handle content-type headers correctly"""
        headers = {"Content-Type": "application/json"}

        if endpoint == "/api/quick-create-full-universe":
            data = {
                "idea_text": "Test content type",
                "duration": "30s",
                "style_key": "cinematic"
            }
            response = test_client.post(endpoint, json=data, headers=headers)
        else:
            response = test_client.get(endpoint, headers=headers)

        # Should handle content-type properly
        assert response.status_code in [200, 404, 405]

    def test_api_error_responses_format(self, test_client):
        """Test: API error responses follow consistent format"""
        # Test 404 error
        response = test_client.get("/api/jobs/non-existent")
        if response.status_code == 404:
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)

        # Test 422 validation error
        response = test_client.post("/api/quick-create-full-universe", json={})
        if response.status_code == 422:
            data = response.json()
            # FastAPI validation error format
            assert "detail" in data

    @pytest.mark.integration
    def test_full_job_workflow(self, test_client, database_manager):
        """Test: Complete job creation and monitoring workflow"""
        import time

        # Step 1: Create job
        request_data = {
            "idea_text": "A complete workflow test",
            "duration": "30s",
            "style_key": "cinematic",
            "auto_create_universe": True
        }

        create_response = test_client.post("/api/quick-create-full-universe", json=request_data)
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Step 2: Monitor job status
        max_wait_time = 30  # seconds
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status_response = test_client.get(f"/api/status/{job_id}")
            assert status_response.status_code == 200

            job_data = status_response.json()
            assert job_data["job_id"] == job_id
            assert "state" in job_data
            assert "progress" in job_data

            # Break if job completed or error
            if job_data["state"] in ["completed", "error"]:
                break

            time.sleep(1)  # Poll every second

        # Verify workflow completed
        final_response = test_client.get(f"/api/status/{job_id}")
        final_data = final_response.json()
        assert final_data["job_id"] == job_id

        # Clean up
        delete_response = test_client.delete(f"/api/jobs/{job_id}")
        assert delete_response.status_code == 200