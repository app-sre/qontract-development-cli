from multiprocessing import Process
from pathlib import Path, PosixPath
from typing import Any

import yaml
from rich.console import Console


def path_representer(
    dumper: yaml.representer.BaseRepresenter, data: Any
) -> yaml.nodes.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


yaml.add_representer(PosixPath, path_representer)


def screenshot(output_file: Path, title: str) -> None:
    console.save_svg(str(output_file.with_suffix(".svg")), title=title)


console = Console(record=True)


class EndlessProcess(Process):
    def run(self) -> None:
        if self._target:  # type: ignore[attr-defined]
            while True:
                self._target(*self._args, **self._kwargs)  # type: ignore[attr-defined]
