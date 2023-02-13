# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from argparse import ArgumentParser, Namespace
from pathlib import Path

import click
from jinja2 import Environment, PackageLoader, select_autoescape

from .util import datetime_to_iso


def run(parser: ArgumentParser, args: Namespace):

    target = Path(".") / "new-yabs.yaml"
    target = target.absolute()
    if target.exists():
        click.confirm(f"Overwrite {target} ?", abort=True)

    context = {
        "date": datetime_to_iso(),
        "full_repo_name": "mar10/test-release-tool",
        "github_token_env_name": "GITHUB_OAUTH_TOKEN",
    }
    file_type = click.prompt(
        "Type",
        type=click.Choice({"full", "compact"}),
        default="full",
    )
    click.confirm(f"Create {target} ?", abort=True, default=True)

    _copy_template(f"yabs-{file_type}.yaml", target, context)


def _copy_template(tmpl_name: str, target: Path, ctx: dict) -> None:
    env = Environment(
        loader=PackageLoader("yabs"),  # defaults to 'templates' folder
        autoescape=select_autoescape(),
    )
    template = env.get_template(tmpl_name)
    expanded = template.render(**ctx)
    # logger.info("Writing {:,} bytes to {!r}...".format(len(tmpl), target_path))
    with target.open("wt") as fp:
        fp.write(expanded)
    return
