from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
)

environment = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates"))
)


def template(template_name: str, *args: Any, **kwargs: Any) -> str:
    tmpl = environment.get_template(template_name)
    return tmpl.render(*args, **kwargs)
