class InvalidFromSelectionError(Exception):
    def __init__(self, selection: str, selections: list):
        message = f"Provided {selection} is invalid. Please choose correct one from: {', '.join(selections)}"
        super().__init__(message)

        self.selection = selection
        self.selections = selections


class InvalidPlatformError(InvalidFromSelectionError):
    pass


class AuthorizationFailedError(Exception):
    def __init__(self, code, reason):
        message = f"Authorization failed. {code} by {reason}"
        super().__init__(message)


class UnauthorizedError(AuthorizationFailedError):
    pass
