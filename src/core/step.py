from __future__ import annotations

from abc import ABC, abstractmethod

from .context import StepContext
from .logger import PipelineLogger


class Step(ABC):
    """Abstract Base Class for a single pipeline step.

    Implements the 4-phase lifecycle: setup -> apply -> validate -> persist.
    """

    def __init__(self, logger: PipelineLogger, step_name: str, step_number: int):
        self.logger = logger
        self.step_name = step_name
        self.step_number = step_number
        self.class_name = self.__class__.__name__

    def execute(self, context: StepContext) -> StepContext:
        self.logger.info(
            f"Starting step #{self.step_number}: {self.step_name}", self.class_name
        )
        context = self.setup(context)
        context = self.apply(context)

        self.logger.info(
            f"Validating results for step #{self.step_number}: {self.step_name}",
            self.class_name,
        )
        self.validate(context)

        context = self.persist(context)
        self.logger.info(
            f"Step #{self.step_number}: {self.step_name} finished successfully",
            self.class_name,
        )
        return context

    def setup(self, context: StepContext) -> StepContext:
        return context

    @abstractmethod
    def apply(self, context: StepContext) -> StepContext:
        pass

    @abstractmethod
    def validate(self, context: StepContext) -> None:
        pass

    def persist(self, context: StepContext) -> StepContext:
        return context


