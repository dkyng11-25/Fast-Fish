class DataValidationError(Exception):
    """Raised when data validation fails within a pipeline step.

    The pipeline will stop immediately when this exception is raised.
    """

    pass


