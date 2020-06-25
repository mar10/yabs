# -*- coding: utf-8 -*-
# (c) 2020 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os

from github import Github, GithubObject

from .cmd_common import WorkflowTask, GH_USER_AGENT
from .util import (
    ConfigError,
    check_arg,
    log_dry,
    log_error,
    log_info,
    log_ok,
    log_warning,
)


class GithubReleaseTask(WorkflowTask):
    DEFAULT_OPTS = {
        "gh_auth": None,  # use `config.gh_auth`
        "draft": True,
        "message": "Released {version}\n"
        + "[Commit details](https://github.com/{repo}/compare/{org_tag_name}...{tag_name}).",
        "name": "v{version}",
        "prerelease": None,
        "repo": None,  # `owner/repo`, defaults to yaml setting
        "tag": None,
        "target_commitish": None,
        "upload": None,
    }

    def __init__(self, opts):
        super().__init__(opts)

        opts = self.opts
        check_arg(opts["gh_auth"], (dict, str), or_none=True)
        check_arg(opts["repo"], str, or_none=True)
        check_arg(opts["name"], str)
        check_arg(opts["message"], str)
        check_arg(opts["draft"], bool)
        check_arg(opts["prerelease"], bool, or_none=True)
        check_arg(opts["upload"], list, or_none=True)
        check_arg(opts["target_commitish"], str, or_none=True)
        check_arg(opts["tag"], str, or_none=True)

        upload = opts["upload"]
        if upload:
            unknown = set(upload).difference(set(("sdist", "bdist_wheel", "bdist_msi")))
            if unknown:
                raise RuntimeError(
                    "Unknown upload target(s): {}".format(", ".join(unknown))
                )

    # def to_str(self, context):
    #     add = self.opts["add"] or self.opts["add_known"]
    #     return "{}(add: {}, '{}')".format(
    #         self.__class__.__name__, add, self.opts["message"]
    #     )

    @classmethod
    def register_cli_command(cls, subparsers, parents):
        """"""
        sp = subparsers.add_parser(
            "gh-release", parents=parents, help="create a release on GitHub",
        )
        # sp.add_argument(
        #     "--draft", action="store_true", help="",
        # )
        # sp.add_argument(
        #     "--opts", help="YAML file with conversion options",
        # )
        sp.set_defaults(command=cls.handle_cli_command)

    def run(self, context):
        opts = self.opts

        if context._args.no_release:
            log_warning("`--no-release` was passed: skipping 'gh_release' task.")
            return True

        ok = True
        # GitHub access token
        auth = opts["gh_auth"]
        if auth:
            if isinstance(auth, dict):
                token = os.environ.get(auth["oauth_token_var"])
            else:
                token = auth
        else:
            token = context.gh_auth_token
        gh = Github(token, user_agent=GH_USER_AGENT)

        repo_name = opts.get("repo") or context.repo
        if not repo_name or "/" not in repo_name:
            raise ConfigError("Missing repo name (expected `GH-USER/PROJECT`).")

        repo = gh.get_repo(repo_name, lazy=False)
        if not repo:
            raise ConfigError("Could not open repo '{}'.".format(repo_name))

        # collaborators = repo.get_collaborators("all")
        # for collab in collaborators:
        #     print(collab)

        # releases = repo.get_releases()
        # for release in releases:
        #     print(release)

        # branches = repo.get_branches()
        # for branch in branches:
        #     print(branch)

        tag_name = context.tag_name
        if not tag_name:
            log_error("Please run 'tag' task first, to create a new tag.")
            return False

        gh_tag = None
        for t in repo.get_tags():
            # print("GH tag", t)
            if t.name == tag_name:
                gh_tag = t

        if self.dry_run:
            log_dry("create_git_release({})".format(gh_tag))
            return True

        if not gh_tag:
            log_error(
                "Could not find tag '{}' on Github (did you run 'bump' and 'tag' tasks first?)".format(
                    tag_name
                )
            )
            return False

        target_commitish = opts["target_commitish"] or GithubObject.NotSet

        prerelease = opts["prerelease"]
        if prerelease is None:
            prerelease = "-" in tag_name or "+" in tag_name
            log_info("Tag '{}': assuming prerelease={}".format(tag_name, prerelease))

        name = opts["name"].format(**vars(context))
        message = opts["message"].format(**vars(context))

        # gh_tag = repo.get_git_tag()
        gh_release = repo.create_git_release(
            tag=tag_name,
            name=name,
            message=message,
            draft=opts["draft"],
            prerelease=prerelease,
            target_commitish=target_commitish,
        )

        if opts["upload"]:
            for target in opts["upload"]:
                path = context.artefacts.get(target)
                if not path or not os.path.isfile(path):
                    raise RuntimeError("Artefact not found: {}".format(path))
                gh_asset = gh_release.upload_asset(
                    str(path),
                    label="",
                    # content_type=NotSet,
                    # name=NotSet,
                )
                log_ok("Upload asset {}".format(gh_asset))

        return ok
