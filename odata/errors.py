class InvalidFromSelectionError(Exception):
    def __init__(self, selection: str, selections: list):
        message = f"Provided {selection} is invalid. Please choose correct one from: {', '.join(selections)}"
        super().__init__(message)

        self.selection = selection
        self.selections = selections


class InvalidNumberError(Exception):
    def __init__(self, selection: int, selections: list):
        message = (f"Provided number {selection} is invalid. Please choose correct one from range "
                   f"{' and '.join(selections)}")
        super().__init__(message)

        self.provided = selection
        self.range = selections


class InvalidPlatformError(InvalidFromSelectionError):
    pass


class AuthorizationFailedError(Exception):
    def __init__(self, code, reason):
        message = f"Authorization failed. {code} by {reason}"
        super().__init__(message)


class UnauthorizedError(AuthorizationFailedError):
    pass


class ParameterReadOnlyError(Exception):
    pass