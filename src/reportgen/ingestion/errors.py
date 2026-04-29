class InputValidationError(ValueError):
    """Raised when input files are structurally valid but fail business validation."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        joined = "\n".join(f"- {error}" for error in self.errors)
        return f"Input validation failed:\n{joined}"
