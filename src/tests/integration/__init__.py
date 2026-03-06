"""
Integration Tests Module

Tests for full pipeline, concurrency, error paths, and benchmarks.
"""

from tests.integration.test_pipeline import (
    TestFullPipeline,
    TestJobStateTransitions,
    TestSessionRecovery,
    TestReportGeneration,
    TestEventSourcingIntegration,
)

from tests.integration.test_concurrency import (
    TestConcurrentJobProcessing,
    TestQueueOrdering,
    TestRaceConditions,
    TestCircuitBreakerConcurrency,
    TestDatabaseConcurrency,
    TestMemoryUnderLoad,
)

from tests.integration.test_error_paths import (
    TestExceptionHandlers,
    TestCircuitBreakerErrors,
    TestCircuitBreakerRegistry,
    TestSagaCompensation,
    TestTimeoutHandling,
    TestErrorMessageQuality,
    TestGracefulDegradation,
)

from tests.integration.test_benchmarks import (
    TestJobLatencyBenchmarks,
    TestQueueThroughputBenchmarks,
    TestEventSourcingBenchmarks,
    TestDatabaseQueryBenchmarks,
    TestMemoryUsageBenchmarks,
    TestCircuitBreakerBenchmarks,
    TestEndToEndBenchmarks,
)

__all__ = [
    'TestFullPipeline',
    'TestJobStateTransitions',
    'TestSessionRecovery',
    'TestReportGeneration',
    'TestEventSourcingIntegration',
    'TestConcurrentJobProcessing',
    'TestQueueOrdering',
    'TestRaceConditions',
    'TestCircuitBreakerConcurrency',
    'TestDatabaseConcurrency',
    'TestMemoryUnderLoad',
    'TestExceptionHandlers',
    'TestCircuitBreakerErrors',
    'TestCircuitBreakerRegistry',
    'TestSagaCompensation',
    'TestTimeoutHandling',
    'TestErrorMessageQuality',
    'TestGracefulDegradation',
    'TestJobLatencyBenchmarks',
    'TestQueueThroughputBenchmarks',
    'TestEventSourcingBenchmarks',
    'TestDatabaseQueryBenchmarks',
    'TestMemoryUsageBenchmarks',
    'TestCircuitBreakerBenchmarks',
    'TestEndToEndBenchmarks',
]
