from typing import Tuple
from rich import progress

__all__ = ["Progress"]


class Progress(progress.Progress):
    @classmethod
    def get_default_columns(cls) -> Tuple[progress.ProgressColumn, ...]:
        return (
            progress.TextColumn("[progress.description]{task.description}"),
            progress.BarColumn(),
            progress.TextColumn("[progress.percentage]{task.completed}/{task.total}"),
            progress.TimeRemainingColumn(),
        )
