from typing import Protocol

from shared.python.ids import JobId


class TrainingProtocol(Protocol):
    def run(self, job_id: JobId) -> None: ...
