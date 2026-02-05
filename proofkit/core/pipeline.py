"""Pipeline execution utilities for ProofKit."""

from typing import List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum

from proofkit.utils.logger import logger


class PipelineStage(str, Enum):
    """Stages of the audit pipeline."""
    COLLECT = "collect"
    ANALYZE = "analyze"
    NARRATE = "narrate"
    REPORT = "report"


@dataclass
class StageResult:
    """Result of a pipeline stage execution."""
    stage: PipelineStage
    success: bool
    data: Any = None
    error: Optional[str] = None


class Pipeline:
    """
    Configurable pipeline for executing audit stages.
    """

    def __init__(self):
        self.stages: List[tuple[PipelineStage, Callable]] = []
        self.results: List[StageResult] = []

    def add_stage(self, stage: PipelineStage, handler: Callable) -> "Pipeline":
        """Add a stage to the pipeline."""
        self.stages.append((stage, handler))
        return self

    def run(
        self,
        initial_data: Any = None,
        progress_callback: Optional[Callable[[PipelineStage, int], None]] = None,
    ) -> List[StageResult]:
        """
        Run all pipeline stages in order.

        Args:
            initial_data: Initial data to pass to first stage
            progress_callback: Optional callback for progress updates

        Returns:
            List of StageResult for each stage
        """
        self.results = []
        current_data = initial_data

        for i, (stage, handler) in enumerate(self.stages):
            logger.info(f"Running pipeline stage: {stage.value}")

            if progress_callback:
                progress = int((i / len(self.stages)) * 100)
                progress_callback(stage, progress)

            try:
                result_data = handler(current_data)
                result = StageResult(
                    stage=stage,
                    success=True,
                    data=result_data,
                )
                current_data = result_data
            except Exception as e:
                logger.error(f"Pipeline stage {stage.value} failed: {e}")
                result = StageResult(
                    stage=stage,
                    success=False,
                    error=str(e),
                )
                self.results.append(result)
                break

            self.results.append(result)

        if progress_callback:
            progress_callback(PipelineStage.REPORT, 100)

        return self.results

    def get_result(self, stage: PipelineStage) -> Optional[StageResult]:
        """Get result for a specific stage."""
        for result in self.results:
            if result.stage == stage:
                return result
        return None

    @property
    def success(self) -> bool:
        """Check if all stages completed successfully."""
        return all(r.success for r in self.results)

    @property
    def last_error(self) -> Optional[str]:
        """Get the error from the last failed stage."""
        for result in reversed(self.results):
            if not result.success:
                return result.error
        return None
