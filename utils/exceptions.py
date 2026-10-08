"""Custom exceptions for HeartGuard.

Provides controlled exceptions for data validation, schema errors,
and dataset loading failures.
"""


class HeartGuardError(Exception):
    """Base exception for all HeartGuard errors."""


class DatasetNotFoundError(HeartGuardError):
    """Raised when a dataset file is not found."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Dataset not found: {path}")


class DatasetEmptyError(HeartGuardError):
    """Raised when a dataset file is empty."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Dataset file is empty: {path}")


class DatasetFormatError(HeartGuardError):
    """Raised when a dataset file cannot be parsed."""

    def __init__(self, path: str, reason: str = "") -> None:
        self.path = path
        self.reason = reason
        msg = f"Cannot parse dataset: {path}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)


class DatasetSchemaError(HeartGuardError):
    """Raised when a dataset is missing required columns."""

    def __init__(self, missing_columns: list[str], dataset_name: str = "dataset") -> None:
        self.missing_columns = missing_columns
        self.dataset_name = dataset_name
        cols = ", ".join(sorted(missing_columns))
        super().__init__(
            f"Missing required {dataset_name} feature(s): {cols}"
        )


class DataValidationError(HeartGuardError):
    """Raised when data validation fails."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        self.details = details or {}
        super().__init__(message)
