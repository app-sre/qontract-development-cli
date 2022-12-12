import logging
from multiprocessing import Process
from pathlib import Path
from typing import (
    Callable,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from rich.logging import RichHandler
from watchfiles import (
    Change,
    DefaultFilter,
    watch,
)

log = logging.getLogger(__name__)


class ExtensionFilter(DefaultFilter):
    def __init__(
        self,
        *,
        extensions: Sequence[str],
        ignore_paths: Optional[Sequence[Union[str, Path]]] = None,
    ) -> None:
        self.extensions = tuple(extensions)
        super().__init__(ignore_paths=ignore_paths)

    def __call__(self, change: Change, path: str) -> bool:
        return path.endswith(self.extensions) and super().__call__(change, path)


def _watcher(
    path: Path, extensions: Sequence[str], action: Callable, action_args: Tuple
):
    # logger must be setup in child process
    logging.basicConfig(
        level="INFO",
        format="%(name)-20s: %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    for changes in watch(path, watch_filter=ExtensionFilter(extensions=extensions)):
        for change in changes:
            log.info(f"{change[1]} changed")
        action(*action_args)


def watch_files(
    path: Path, extensions: Sequence[str], action: Callable, action_args: Tuple
) -> Process:
    p = Process(target=_watcher, args=(path, extensions, action, action_args))
    p.start()
    return p
