"""Stable failures without reflected filesystem or credential details."""


class StorageError(Exception):
    def __init__(self, code, status=409):
        super().__init__(code)
        self.code = code
        self.status = status
