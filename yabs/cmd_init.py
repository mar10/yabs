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


def handle_init_command(parser: ArgumentParser, args: Namespace):
    res = run(parser, args)
    return res


def run(parser: ArgumentParser, args: Namespace):

    target = Path(args.filename)
    # target = Path(".") / "new-yabs.yaml"
    target = target.absolute()
    if not target.suffix:
        target = target.with_suffix(".yaml")
    if target.suffix != ".yaml":
        raise click.BadArgumentUsage(f"Expected `.yaml` extension: {target}")
    if target.exists():
        click.confirm(f"Overwrite {target} ?", abort=True)
    else:
        click.echo(f"Creating {target}...")

    full_repo_name = click.prompt("GitHub Repo name (format: USER/PROJECT)", type=str)
    if full_repo_name.count("/") != 1:
        raise click.BadParameter(full_repo_name)

    github_token_env_name = click.prompt(
        "GitHub OAUTH token environment variable", default="GITHUB_OAUTH_TOKEN"
    )

    context = {
        "date": datetime_to_iso(),
        "full_repo_name": full_repo_name,
        "github_token_env_name": github_token_env_name,
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
