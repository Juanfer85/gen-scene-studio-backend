"""
Load testing scenarios for Gen Scene Studio backend.

Tests realistic usage patterns, concurrent user behavior,
and system performance under various load conditions.
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from httpx import AsyncClient
from tests.conftest import (
    test_client, database_manager,
    TestDataFactory, DatabaseTestScenarios,
    PerformanceTestHelper, AsyncTestHelper
)
from models.entities import Job, JobState, Render, RenderStatus


class TestLoadScenarios:
    """Load testing scenarios for backend performance."""

    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_job_creation_load(self, test_client, database_manager):
        """Test: Concurrent job creation under moderate load"""
        # Arrange
        num_concurrent_jobs = 50
        num_requests_per_job = 2

        async def create_job_job(batch_id: int):
            """Create multiple jobs in a batch."""
            request_data = {
                "idea_text": f"Load test batch {batch_id}",
                "duration": "30s",
                "style_key": "cinematic",
                "auto_create_universe": True
            }

            responses = []
            for i in range(num_requests_per_job):
                try:
                    response = await test_client.post(
                        "/api/quick-create-full-universe",
                        json=request_data
                    )
                    responses.append(response)
                except Exception as e:
                    responses.append({"error": str(e)})

            return responses

        # Act
        start_time = time.time()

        # Create jobs concurrently
        tasks = [
            create_job_job(batch_id=i)
            for i in range(num_concurrent_jobs // num_requests_per_job)
        ]

        all_responses = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Assert
        total_time = end_time - start_time
        total_requests = num_concurrent_jobs

        # Count successful responses
        successful_responses = []
        failed_responses = []

        for responses in all_responses:
            if isinstance(responses, list):
                for response in responses:
                    if hasattr(response, 'status_code'):
                        if response.status_code == 200:
                            successful_responses.append(response)
                        else:
                            failed_responses.append(response)
                    else:
                        failed_responses.append({"error": "No status code"})
            else:
                failed_responses.append({"error": str(responses)})

        # Performance assertions
        success_rate = len(successful_responses) / total_requests
        avg_response_time = total_time / total_requests if total_requests > 0 else 0
        requests_per_second = total_requests / total_time if total_time > 0 else 0

        assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"
        assert total_time < 30.0, f"Total time too long: {total_time:.2f}s"
        assert avg_response_time < 1.0, f"Average response time too high: {avg_response_time:.3f}s"
        assert requests_per_second >= 2.0, f"Requests per second too low: {requests_per_second:.2f}"

        print(f"Load test results:")
        print(f"  Total requests: {total_requests}")
        print(f"  Successful: {len(successful_responses)} ({success_rate:.2%})")
        print(f"  Failed: {len(failed_responses)}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Requests/sec: {requests_per_second:.2f}")

    @pytest.mark.performance
    @pytest.mark.slow
    async def test_job_status_polling_load(self, test_client, database_manager):
        """Test: High-frequency job status polling"""
        # Arrange - Create jobs for polling
        job_repo = database_manager.jobs()
        num_jobs = 20

        jobs = []
        for i in range(num_jobs):
            job = TestDataFactory.create_job(f"polling-job-{i}")
            job_repo.create(job)
            jobs.append(job)

        # Wait a moment for jobs to be processed
        await asyncio.sleep(1)

        async def poll_job(job: Job):
            """Poll a single job status repeatedly."""
            poll_count = 0
            max_polls = 10

            for _ in range(max_polls):
                try:
                    response = await test_client.get(f"/api/status/{job.job_id}")
                    if response.status_code == 200:
                        poll_count += 1
                    else:
                        break
                except Exception:
                    break
                await asyncio.sleep(0.1)  # Poll every 100ms

            return poll_count

        # Act
        start_time = time.time()

        # Poll all jobs concurrently
        tasks = [poll_job(job) for job in jobs]
        poll_results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Assert
        total_time = end_time - start_time
        total_polls = sum(result for result in poll_results if isinstance(result, int))
        polls_per_second = total_polls / total_time if total_time > 0 else 0

        assert total_time < 15.0, f"Polling took too long: {total_time:.2f}s"
        assert polls_per_second >= 100.0, f"Polling rate too low: {polls_per_second:.2f} polls/sec"
        assert total_polls >= num_jobs * 5, f"Too few polls completed: {total_polls}"

        print(f"Polling load test results:")
        print(f"  Total polls: {total_polls}")
        print(f"  Polls/sec: {polls_per_second:.2f}")
        print(f"  Total time: {total_time:.2f}s")

    @pytest.mark.performance
    @pytest.mark.slow
    async def test_mixed_workload_simulation(self, test_client, database_manager):
        """Test: Simulate realistic mixed workload"""
        # Arrange
        job_repo = database_manager.jobs()
        render_repo = database_manager.renders()

        # Create initial jobs
        existing_jobs = []
        for i in range(10):
            job = TestDataFactory.create_job(f"mixed-job-{i}")
            job_repo.create(job)
            existing_jobs.append(job)

        # Add some renders to simulate work
        for job in existing_jobs[:5]:
            render = TestDataFactory.create_render(job.job_id, f"render-{job.job_id}")
            render_repo.create(render)

        async def simulate_user_behavior():
            """Simulate realistic user behavior patterns."""
            actions = []

            # 60%: Job status checks
            for job in existing_jobs:
                if statistics.random() < 0.6:
                    actions.append(test_client.get(f"/api/status/{job.job_id}"))

            # 25%: New job creation
            if statistics.random() < 0.25:
                actions.append(test_client.post(
                    "/api/quick-create-full-universe",
                    json={
                        "idea_text": f"Simulated job {time.time()}",
                        "duration": "30s",
                        "style_key": "cinematic",
                        "auto_create_universe": True
                    }
                ))

            # 10%: List jobs
            if statistics.random() < 0.1:
                actions.append(test_client.get("/api/jobs?limit=10"))

            # 5%: Jobs hub request
            if statistics.random() < 0.05:
                actions.append(test_client.get("/api/jobs-hub"))

            # Execute actions with realistic timing
            for action in actions:
                await action
                await asyncio.sleep(statistics.uniform(0.1, 2.0))  # Realistic user delay

            return len(actions)

        # Act
        start_time = time.time()

        # Simulate 50 concurrent users
        num_concurrent_users = 50
        tasks = [simulate_user_behavior() for _ in range(num_concurrent_users)]

        action_counts = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # Assert
        total_time = end_time - start_time
        successful_sims = sum(count for count in action_counts if isinstance(count, int))
        total_actions = successful_sims
        actions_per_second = total_actions / total_time if total_time > 0 else 0

        assert total_time < 60.0, f"Mixed workload took too long: {total_time:.2f}s"
        assert actions_per_second >= 5.0, f"Actions per second too low: {actions_per_second:.2f}"
        assert successful_sims >= num_concurrent_users * 0.8, f"Too few simulations completed"

        print(f"Mixed workload simulation results:")
        print(f"  Concurrent users: {num_concurrent_users}")
        print(f"  Total actions: {total_actions}")
        print(f"  Actions/sec: {actions_per_second:.2f}")
        print(f"  Total time: {total_time:.2f}s")

    @pytest.mark.performance
    @pytest.mark.slow
    async def test_database_connection_pool_stress(self, database_manager):
        """Test: Database connection pool under stress"""
        import threading
        import queue

        num_threads = 20
        operations_per_thread = 50
        results = queue.Queue()

        def worker_thread(thread_id: int):
            """Worker thread that stresses the database."""
            job_repo = database_manager.jobs()
            success_count = 0
            error_count = 0

            for i in range(operations_per_thread):
                try:
                    # Create and retrieve job
                    job = TestDataFactory.create_job(f"stress-job-{thread_id}-{i}")
                    job_repo.create(job)

                    # Retrieve job
                    retrieved = job_repo.get_by_id(job.job_id)
                    if retrieved:
                        success_count += 1
                    else:
                        error_count += 1

                    # Update job
                    job_repo.update_progress(job.job_id, 50)
                    success_count += 1

                except Exception as e:
                    error_count += 1

            results.put({
                'thread_id': thread_id,
                'success_count': success_count,
                'error_count': error_count,
                'total_operations': operations_per_thread * 3  # create, retrieve, update
            })

        # Act
        start_time = time.time()
        threads = []

        # Start worker threads
        for i in range(num_threads):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        end_time = time.time()

        # Collect results
        thread_results = []
        while not results.empty():
            thread_results.append(results.get())

        # Assert
        total_time = end_time - start_time
        total_operations = sum(result['total_operations'] for result in thread_results)
        total_successes = sum(result['success_count'] for result in thread_results)
        total_errors = sum(result['error_count'] for result in thread_results)

        operations_per_second = total_operations / total_time if total_time > 0 else 0
        success_rate = total_successes / total_operations if total_operations > 0 else 0

        assert total_time < 30.0, f"Database stress test took too long: {total_time:.2f}s"
        assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"
        assert operations_per_second >= 100.0, f"Operations per second too low: {operations_per_second:.2f}"

        print(f"Database connection pool stress results:")
        print(f"  Threads: {num_threads}")
        print(f"  Total operations: {total_operations}")
        print(f"  Success rate: {success_rate:.2%}")
        print(f"  Operations/sec: {operations_per_second:.2f}")
        print(f"  Total time: {total_time:.2f}s")

    @pytest.mark.performance
    def test_memory_usage_under_load(self, database_manager):
        """Test: Memory usage during extended load"""
        import psutil
        import os

        job_repo = database_manager.jobs()
        initial_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB

        # Create large dataset
        num_jobs = 1000
        created_jobs = []

        for i in range(num_jobs):
            job = TestDataFactory.create_job(f"memory-test-job-{i}")
            job_repo.create(job)
            created_jobs.append(job.job_id)

            # Periodically check memory
            if i % 100 == 0:
                current_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                memory_increase = current_memory - initial_memory
                print(f"Jobs created: {i}, Memory increase: {memory_increase:.2f} MB")

        peak_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        # Clean up some jobs
        for job_id in created_jobs[:500]:
            job_repo.delete(job_id)

        final_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        # Assert
        memory_efficiency = num_jobs / (peak_memory - initial_memory) if peak_memory > initial_memory else num_jobs

        assert memory_efficiency > 10, f"Memory efficiency too low: {memory_efficiency:.2f} jobs/MB"
        assert final_memory < peak_memory, f"Memory not properly cleaned up"

        print(f"Memory usage test results:")
        print(f"  Jobs created: {num_jobs}")
        print(f"  Initial memory: {initial_memory:.2f} MB")
        print(f"  Peak memory: {peak_memory:.2f} MB")
        print(f"  Final memory: {final_memory:.2f} MB")
        print(f"  Memory efficiency: {memory_efficiency:.2f} jobs/MB")

    @pytest.mark.performance
    @pytest.mark.slow
    async def test_system_degradation_under_load(self, test_client, database_manager):
        """Test: System performance degradation under increasing load"""
        load_levels = [10, 25, 50, 100]
        results = {}

        for load_level in load_levels:
            async def single_request():
                try:
                    start = time.time()
                    response = await test_client.get("/health")
                    end = time.time()
                    return {
                        'response_time': end - start,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    }
                except Exception as e:
                    return {
                        'response_time': 999.0,
                        'status_code': 500,
                        'success': False,
                        'error': str(e)
                    }

            # Run concurrent requests
            tasks = [single_request() for _ in range(load_level)]
            start_time = time.time()

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            # Analyze results
            successful = [r for r in responses if isinstance(r, dict) and r.get('success', False)]
            response_times = [r['response_time'] for r in successful]

            avg_response_time = statistics.mean(response_times) if response_times else 0
            p95_response_time = statistics.quantiles(response_times, 0.95) if len(response_times) >= 20 else 0
            p99_response_time = statistics.quantiles(response_times, 0.99) if len(response_times) >= 100 else 0

            total_time = end_time - start_time
            requests_per_second = len(successful) / total_time if total_time > 0 else 0

            results[load_level] = {
                'load_level': load_level,
                'avg_response_time': avg_response_time,
                'p95_response_time': p95_response_time,
                'p99_response_time': p99_response_time,
                'requests_per_second': requests_per_second,
                'success_rate': len(successful) / load_level
            }

            print(f"Load level {load_level}: avg={avg_response_time:.3f}s, rps={requests_per_second:.2f}")

            # Wait between load tests
            await asyncio.sleep(5)

        # Assert performance degradation is acceptable
        for load_level, metrics in results.items():
            assert metrics['success_rate'] >= 0.95, f"Success rate too low at load {load_level}: {metrics['success_rate']:.2%}"
            assert metrics['avg_response_time'] < 2.0, f"Average response time too high at load {load_level}: {metrics['avg_response_time']:.3f}s"
            assert metrics['p95_response_time'] < 5.0, f"P95 response time too high at load {load_level}: {metrics['p95_response_time']:.3f}s"

        # Check that performance doesn't degrade excessively
        if len(results) >= 2:
            load_levels_sorted = sorted(results.keys())
            low_load = results[load_levels_sorted[0]]
            high_load = results[load_levels_sorted[-1]]

            avg_degradation = low_load['avg_response_time'] / high_load['avg_response_time']
            rps_degradation = high_load['requests_per_second'] / low_load['requests_per_second']

            assert avg_degradation >= 0.5, f"Excessive average response time degradation: {avg_degradation:.2f}x"
            assert rps_degradation >= 0.2, f"Excessive RPS degradation: {rps_degradation:.2f}x"

        print(f"System degradation test completed successfully")