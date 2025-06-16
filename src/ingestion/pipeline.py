# src/ingestion/pipeline.py
# Defines the core modular ingestion pipeline structure.

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from loguru import logger

class IngestionContext:
    """
    A data-carrying object that flows through the ingestion pipeline.
    Each step can read from and write to this context.
    """
    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        self._data = initial_data if initial_data is not None else {}
        self.errors: List[Exception] = []
        self.is_aborted = False

    def set(self, key: str, value: Any):
        """Set a value in the context."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the context."""
        return self._data.get(key, default)

    def add_error(self, error: Exception):
        """Record an error that occurred during a step."""
        self.errors.append(error)

    def abort(self):
        """Signal that the pipeline should stop processing."""
        self.is_aborted = True

    def __repr__(self):
        return f"IngestionContext(data={self._data.keys()}, errors={len(self.errors)}, aborted={self.is_aborted})"


class IngestionStep(ABC):
    """Abstract base class for a single step in the ingestion pipeline."""

    @abstractmethod
    async def run(self, context: IngestionContext) -> IngestionContext:
        """
        Executes the step's logic.

        Args:
            context: The shared context from the pipeline.

        Returns:
            The modified context.
        """
        pass

    @property
    def name(self) -> str:
        """Returns the name of the step."""
        return self.__class__.__name__


class IngestionPipeline:
    """Orchestrates a series of ingestion steps."""

    def __init__(self, steps: List[IngestionStep]):
        self.steps = steps

    async def run(self, initial_context: Optional[Dict[str, Any]] = None) -> IngestionContext:
        """Runs the entire pipeline, executing each step in order."""
        context = IngestionContext(initial_data=initial_context)
        logger.info(f"Starting ingestion pipeline with steps: {[step.name for step in self.steps]}")

        for step in self.steps:
            if context.is_aborted:
                logger.warning(f"Pipeline aborted. Skipping remaining steps starting from '{step.name}'.")
                break
            
            try:
                logger.info(f"--- Running step: {step.name} ---")
                context = await step.run(context)
                logger.info(f"--- Finished step: {step.name} ---")
            except Exception as e:
                logger.error(f"Error during step '{step.name}': {e}", exc_info=True)
                context.add_error(e)
                context.abort() # Abort pipeline on step failure

        logger.info("Ingestion pipeline finished.")
        if context.errors:
            logger.error(f"Pipeline completed with {len(context.errors)} errors.")
        
        return context
