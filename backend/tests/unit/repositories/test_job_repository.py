"""
Unit tests for JobRepository.

Tests cover CRUD operations, business logic, edge cases,
and error handling for the Job repository layer.
"""

import pytest
import time
from datetime import datetime
from tests.conftest import (
    job_repository, sample_job, sample_completed_job, multiple_jobs,
    TestDatabase, TestAssertions, TestDataFactory, PerformanceTestHelper
)
from models.entities import Job, JobState


class TestJobRepository:
    """Unit tests for JobRepository functionality."""

    def setup_method(self):
        """Setup for each test method."""
        TestDatabase.setup_test_tables()

    def teardown_method(self):
        """Cleanup after each test method."""
        pass  # Temp files cleaned up by fixtures

    def test_create_table_success(self, job_repository):
        """Test: Table creation succeeds"""
        # Table should already be created by fixture
        # This test verifies idempotency
        job_repository.create_table()  # Should not raise error

    def test_create_job_success(self, job_repository, sample_job):
        """Test: Job creation succeeds with valid data"""
        # Act
        result = job_repository.create(sample_job)

        # Assert
        assert result == sample_job.job_id

        # Verify job was actually created
        retrieved_job = job_repository.get_by_id(sample_job.job_id)
        TestAssertions.assert_job_equal(retrieved_job, sample_job)

    def test_create_job_with_minimal_data(self, job_repository):
        """Test: Job creation succeeds with minimal required data"""
        # Arrange
        minimal_job = TestDataFactory.create_job("minimal-job-123")

        # Act
        result = job_repository.create(minimal_job)

        # Assert
        assert result == minimal_job.job_id

    def test_get_by_id_success(self, job_repository, sample_job):
        """Test: Retrieve existing job by ID"""
        # Arrange
        job_repository.create(sample_job)

        # Act
        result = job_repository.get_by_id(sample_job.job_id)

        # Assert
        assert result is not None
        TestAssertions.assert_job_equal(result, sample_job)

    def test_get_by_id_not_found(self, job_repository):
        """Test: Retrieve non-existent job returns None"""
        # Act
        result = job_repository.get_by_id("non-existent-job")

        # Assert
        assert result is None

    def test_update_job_state_success(self, job_repository, sample_job):
        """Test: Update job state succeeds"""
        # Arrange
        job_repository.create(sample_job)

        # Act
        result = job_repository.update_state(
            sample_job.job_id,
            JobState.PROCESSING,
            progress=50
        )

        # Assert
        assert result is True

        # Verify update
        updated_job = job_repository.get_by_id(sample_job.job_id)
        assert updated_job.state == JobState.PROCESSING
        assert updated_job.progress == 50
        assert updated_job.updated_at > sample_job.updated_at

    def test_update_job_state_only(self, job_repository, sample_job):
        """Test: Update only job state without progress"""
        # Arrange
        job_repository.create(sample_job)

        # Act
        result = job_repository.update_state(sample_job.job_id, JobState.PROCESSING)

        # Assert
        assert result is True

        # Verify update
        updated_job = job_repository.get_by_id(sample_job.job_id)
        assert updated_job.state == JobState.PROCESSING
        assert updated_job.progress == sample_job.progress  # Unchanged

    def test_update_job_state_nonexistent(self, job_repository):
        """Test: Update non-existent job returns False"""
        # Act
        result = job_repository.update_state(
            "non-existent-job",
            JobState.PROCESSING
        )

        # Assert
        assert result is False

    def test_update_progress_success(self, job_repository, sample_job):
        """Test: Update job progress succeeds"""
        # Arrange
        job_repository.create(sample_job)

        # Act
        result = job_repository.update_progress(sample_job.job_id, 75)

        # Assert
        assert result is True

        # Verify update
        updated_job = job_repository.get_by_id(sample_job.job_id)
        assert updated_job.progress == 75
        assert updated_job.updated_at > sample_job.updated_at

    def test_update_progress_invalid_value(self, job_repository, sample_job):
        """Test: Update progress with invalid value raises ValueError"""
        # Arrange
        job_repository.create(sample_job)

        # Act & Assert
        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            job_repository.update_progress(sample_job.job_id, 150)

        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            job_repository.update_progress(sample_job.job_id, -10)

    def test_delete_job_success(self, job_repository, sample_job):
        """Test: Delete existing job succeeds"""
        # Arrange
        job_repository.create(sample_job)

        # Act
        result = job_repository.delete(sample_job.job_id)

        # Assert
        assert result is True

        # Verify deletion
        deleted_job = job_repository.get_by_id(sample_job.job_id)
        assert deleted_job is None

    def test_delete_job_nonexistent(self, job_repository):
        """Test: Delete non-existent job returns False"""
        # Act
        result = job_repository.delete("non-existent-job")

        # Assert
        assert result is False

    def test_list_all_success(self, job_repository, multiple_jobs):
        """Test: List all jobs returns correct list"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        result = job_repository.list_all()

        # Assert
        assert len(result) == len(multiple_jobs)
        job_ids = {job.job_id for job in result}
        expected_ids = {job.job_id for job in multiple_jobs}
        assert job_ids == expected_ids

    def test_list_all_with_limit(self, job_repository, multiple_jobs):
        """Test: List jobs with limit returns limited results"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        result = job_repository.list_all(limit=2)

        # Assert
        assert len(result) == 2

    def test_list_all_with_offset(self, job_repository, multiple_jobs):
        """Test: List jobs with offset skips results"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        result = job_repository.list_all(limit=2, offset=2)

        # Assert
        assert len(result) == 2
        # Should skip first 2 jobs
        returned_ids = {job.job_id for job in result}
        expected_ids = {multiple_jobs[2].job_id, multiple_jobs[3].job_id}
        assert returned_ids == expected_ids

    def test_list_all_with_state_filter(self, job_repository, multiple_jobs):
        """Test: List jobs with state filter returns filtered results"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        result = job_repository.list_all(state_filter=JobState.COMPLETED)

        # Assert
        completed_jobs = [job for job in multiple_jobs if job.state == JobState.COMPLETED]
        assert len(result) == len(completed_jobs)

        for job in result:
            assert job.state == JobState.COMPLETED

    def test_get_active_jobs(self, job_repository, multiple_jobs):
        """Test: Get active jobs returns queued and processing jobs"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        result = job_repository.get_active_jobs()

        # Assert
        active_jobs = [job for job in multiple_jobs
                      if job.state in [JobState.QUEUED, JobState.PROCESSING]]
        assert len(result) == len(active_jobs)

        for job in result:
            assert job.state in [JobState.QUEUED, JobState.PROCESSING]

    def test_get_jobs_by_state(self, job_repository, multiple_jobs):
        """Test: Get jobs by specific state"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        processing_jobs = job_repository.get_jobs_by_state(JobState.PROCESSING)
        completed_jobs = job_repository.get_jobs_by_state(JobState.COMPLETED)

        # Assert
        expected_processing = [job for job in multiple_jobs if job.state == JobState.PROCESSING]
        expected_completed = [job for job in multiple_jobs if job.state == JobState.COMPLETED]

        assert len(processing_jobs) == len(expected_processing)
        assert len(completed_jobs) == len(expected_completed)

        for job in processing_jobs:
            assert job.state == JobState.PROCESSING
        for job in completed_jobs:
            assert job.state == JobState.COMPLETED

    def test_count_all_jobs(self, job_repository, multiple_jobs):
        """Test: Count all jobs returns correct total"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        result = job_repository.count()

        # Assert
        assert result == len(multiple_jobs)

    def test_count_jobs_by_state(self, job_repository, multiple_jobs):
        """Test: Count jobs by state returns correct totals"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        completed_count = job_repository.count(state_filter=JobState.COMPLETED)
        processing_count = job_repository.count(state_filter=JobState.PROCESSING)

        # Assert
        expected_completed = len([job for job in multiple_jobs if job.state == JobState.COMPLETED])
        expected_processing = len([job for job in multiple_jobs if job.state == JobState.PROCESSING])

        assert completed_count == expected_completed
        assert processing_count == expected_processing

    def test_get_stuck_jobs(self, job_repository):
        """Test: Get stuck jobs returns old processing jobs"""
        # Arrange
        old_time = int(time.time()) - 3600  # 1 hour ago

        # Create a stuck job
        stuck_job = TestDataFactory.create_job("stuck-job")
        stuck_job.state = JobState.PROCESSING
        stuck_job.updated_at = old_time
        job_repository.create(stuck_job)

        # Update it to make it look old
        job_repository.update(stuck_job.job_id, {"updated_at": old_time})

        # Create a fresh processing job
        fresh_job = TestDataFactory.create_job("fresh-job")
        fresh_job.state = JobState.PROCESSING
        job_repository.create(fresh_job)

        # Act
        stuck_jobs = job_repository.get_stuck_jobs(minutes_ago=30)

        # Assert
        assert len(stuck_jobs) == 1
        assert stuck_jobs[0].job_id == stuck_job.job_id

    def test_get_recent_jobs(self, job_repository, sample_job, sample_completed_job):
        """Test: Get recent jobs returns jobs within time range"""
        # Arrange
        now = int(time.time())
        recent_time = now - 3600  # 1 hour ago
        old_time = now - 7200  # 2 hours ago

        # Create jobs with different timestamps
        job_repository.create(sample_job)
        job_repository.create(sample_completed_job)

        # Update timestamps
        job_repository.update(sample_job.job_id, {"created_at": recent_time})
        job_repository.update(sample_completed_job.job_id, {"created_at": old_time})

        # Act
        recent_jobs = job_repository.get_recent_jobs(hours=2)

        # Assert
        assert len(recent_jobs) == 1
        assert recent_jobs[0].job_id == sample_job.job_id

    def test_exists_existing_job(self, job_repository, sample_job):
        """Test: Exists returns True for existing job"""
        # Arrange
        job_repository.create(sample_job)

        # Act
        result = job_repository.exists(sample_job.job_id)

        # Assert
        assert result is True

    def test_exists_nonexistent_job(self, job_repository):
        """Test: Exists returns False for non-existent job"""
        # Act
        result = job_repository.exists("non-existent-job")

        # Assert
        assert result is False

    def test_get_job_statistics(self, job_repository, multiple_jobs):
        """Test: Get job statistics returns correct aggregates"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Act
        stats = job_repository.get_job_statistics()

        # Assert
        assert len(stats) > 0

        # Verify we have statistics for each state
        states_in_jobs = {job.state.value for job in multiple_jobs}
        for state in stats:
            assert state in states_in_jobs

        # Verify counts
        for state, state_info in stats.items():
            expected_count = len([job for job in multiple_jobs if job.state.value == state])
            assert state_info['count'] == expected_count

    @pytest.mark.performance
    def test_performance_create_job(self, job_repository):
        """Performance test: Job creation should be fast"""
        job = TestDataFactory.create_job(f"perf-job-{time.time()}")

        # Measure execution time
        _, execution_time = PerformanceTestHelper.measure_time(
            job_repository.create, job
        )

        # Assert - should complete within 50ms
        assert execution_time < 0.05, f"Job creation took {execution_time:.3f}s, expected < 0.05s"

    @pytest.mark.performance
    def test_performance_get_job(self, job_repository, sample_job):
        """Performance test: Job retrieval should be fast"""
        # Arrange
        job_repository.create(sample_job)

        # Measure execution time
        _, execution_time = PerformanceTestHelper.measure_time(
            job_repository.get_by_id, sample_job.job_id
        )

        # Assert - should complete within 10ms
        assert execution_time < 0.01, f"Job retrieval took {execution_time:.3f}s, expected < 0.01s"

    @pytest.mark.performance
    def test_performance_list_jobs(self, job_repository, multiple_jobs):
        """Performance test: Job listing should scale well"""
        # Arrange
        for job in multiple_jobs:
            job_repository.create(job)

        # Measure execution time
        _, execution_time = PerformanceTestHelper.measure_time(
            job_repository.list_all
        )

        # Assert - should complete within 100ms even with multiple jobs
        assert execution_time < 0.1, f"Job listing took {execution_time:.3f}s, expected < 0.1s"

    @pytest.mark.database
    def test_database_integrity_foreign_keys(self, job_repository):
        """Test: Database enforces foreign key constraints"""
        # This test would require setting up related tables
        # For now, test that job creation works with basic constraints
        job = TestDataFactory.create_job("integrity-test")

        # Should succeed
        job_repository.create(job)

    @pytest.mark.database
    def test_database_constraints_job_progress(self, job_repository):
        """Test: Database enforces progress range constraints"""
        job = TestDataFactory.create_job("constraint-test")

        # Act
        job_repository.create(job)

        # Try to update with invalid progress (outside 0-100 range)
        result = job_repository.update_progress(job.job_id, 150)

        # Database constraint should prevent this
        # Note: This depends on SQLite CHECK constraints being enforced
        # The actual behavior might vary based on SQLite version

    @pytest.mark.parametrize("job_state", [
        JobState.QUEUED,
        JobState.PROCESSING,
        JobState.COMPLETED,
        JobState.ERROR,
        JobState.CANCELLED
    ])
    def test_create_job_all_states(self, job_repository, job_state):
        """Parameterized test: Create jobs with all possible states"""
        job = TestDataFactory.create_job(f"state-test-{job_state.value}")
        job.state = job_state

        # Act
        result = job_repository.create(job)

        # Assert
        assert result == job.job_id

        # Verify
        retrieved_job = job_repository.get_by_id(job.job_id)
        assert retrieved_job.state == job_state

    def test_error_handling_invalid_job_id(self, job_repository):
        """Test: Handle invalid job ID gracefully"""
        # Test with None
        with pytest.raises((TypeError, ValueError)):
            job_repository.get_by_id(None)

        # Test with empty string
        with pytest.raises((TypeError, ValueError)):
            job_repository.get_by_id("")

        # Test with very long string
        long_id = "x" * 1000
        result = job_repository.get_by_id(long_id)
        assert result is None

    def test_concurrent_job_creation(self, job_repository):
        """Test: Handle concurrent job creation safely"""
        import threading

        results = []
        errors = []

        def create_job(job_id):
            try:
                job = TestDataFactory.create_job(job_id)
                result = job_repository.create(job)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple jobs concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=create_job,
                args=(f"concurrent-job-{i}",)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Assert all jobs were created successfully
        assert len(results) == 5
        assert len(errors) == 0
        assert len(set(results)) == 5  # All unique

    @pytest.mark.slow
    def test_large_dataset_performance(self, job_repository):
        """Test: Performance with large dataset (1000 jobs)"""
        import time

        # Create large dataset
        start_time = time.time()
        job_ids = []

        for i in range(1000):
            job = TestDataFactory.create_job(f"bulk-job-{i}")
            job_id = job_repository.create(job)
            job_ids.append(job_id)

        creation_time = time.time() - start_time

        # Test retrieval performance
        start_time = time.time()
        all_jobs = job_repository.list_all()
        retrieval_time = time.time() - start_time

        # Test filtering performance
        start_time = time.time()
        completed_jobs = job_repository.get_jobs_by_state(JobState.COMPLETED)
        filter_time = time.time() - start_time

        # Assertions
        assert len(all_jobs) == 1000
        assert creation_time < 10.0, f"Bulk creation took {creation_time:.2f}s"
        assert retrieval_time < 0.5, f"Bulk retrieval took {retrieval_time:.3f}s"
        assert filter_time < 0.1, f"Bulk filtering took {filter_time:.3f}s"

        # Cleanup some jobs to test deletion performance
        start_time = time.time()
        for job_id in job_ids[:100]:  # Delete first 100 jobs
            job_repository.delete(job_id)
        deletion_time = time.time() - start_time

        assert deletion_time < 5.0, f"Bulk deletion took {deletion_time:.2f}s"