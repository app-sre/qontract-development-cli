from multiprocessing import Process
from pathlib import (
    Path,
    PosixPath,
)

import yaml
from rich.console import Console


def path_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


yaml.add_representer(PosixPath, path_representer)


def screenshot(output_file: Path, title: str):
    console.save_svg(str(output_file.with_suffix(".svg")), title=title)


console = Console(record=True)


class EndlessProcess(Process):
    def run(self):
        if self._target:  # type: ignore
            while True:
                self._target(*self._args, **self._kwargs)  # type: ignore
