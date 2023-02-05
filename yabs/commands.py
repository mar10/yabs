# -*- coding: utf-8 -*-
# (c) 2020-2022 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
from argparse import ArgumentParser, Namespace

import requests

from yabs.task.common import REQUESTS_HEADERS, TaskContext
from yabs.task_runner import TaskRunner

from .util import log_error, log_info, log_warning, write


def handle_run_command(parser: ArgumentParser, args: Namespace):
    tm = TaskRunner(args.workflow, parser, args)
    try:
        res = tm.run()
    except KeyboardInterrupt:
        log_error("Aborted by user.")
        if args.verbose >= 2:
            tm._log_task_instances()
        raise
    return res


def handle_info_command(parser: ArgumentParser, args: Namespace):
    tr = TaskRunner(".", parser, args)  # , pick_tasks="check")
    tr.log_final_progress = False

    context = TaskContext(tr)

    if tr.cli_arg("check"):
        # This will also log the info header:
        return tr.run(pick_tasks="check")

    tr.log_header_info(context=context)

    res = context.repo_obj.git.status()
    write("git status", output=res)
    log_info("")

    url = f"https://github.com/{context.repo}/releases/tag/{context.org_tag_name}"
    try:
        resp = requests.get(url, verify=False, headers=REQUESTS_HEADERS)
        resp.raise_for_status()
        log_info(f"GitHub URL: {url}")
    except Exception as e:
        log_warning(f"GitHub URL: {e}")

    url = f"https://pypi.org/project/{context.repo_short}/"
    try:
        resp = requests.get(url, verify=False, headers=REQUESTS_HEADERS)
        resp.raise_for_status()
        log_info(f"PyPI URL:   {url}")
    except Exception as e:
        log_warning(f"PyPI URL:   {e}")

    wgr_inst = tr.get_first_task_instance("winget_release")
    if wgr_inst:
        package_id = wgr_inst.task_def.get("package_id", "")
        package_path_part = package_id.replace(".", "/")
        wpm_version = f"{context.org_tag_name}.0".lstrip("v")
        char0 = context.repo[0]
        url = f"https://github.com/microsoft/winget-pkgs/tree/master/manifests/{char0}/{package_path_part}/{wpm_version}"
        try:
            resp = requests.get(url, verify=False, headers=REQUESTS_HEADERS)
            resp.raise_for_status()
            log_info(f"WPM URL:    {url}")
        except Exception as e:
            log_warning(f"WPM URL:    {e}")
            log_warning("            (Note: package_id is case sensitive)")
    else:
        log_info("`winget_release` is not configured.")

    log_info("")
    log_info("Pass `--check` option for more details.")
    log_info("")

    return 0
