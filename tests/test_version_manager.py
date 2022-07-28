# -*- coding: utf-8 -*-
# (c) 2020-2021 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import os

import pytest
from semantic_version import Version

from yabs.task_runner import TaskRunner


class TestVersionManager:
    def test_basics(self):
        folder = os.path.abspath(os.path.dirname(__file__))

        tr = TaskRunner(os.path.join(folder, "fixtures/yabs_1.yaml"))

        assert tr.yaml.get("file_version") == "yabs#1"
        with pytest.raises(KeyError):
            tr.get_config("foobar")
        assert tr.get_config("foobar", None) is None

        version_manager = tr.version_manager
        assert version_manager
        assert len(version_manager.parsers) == 1
        vp = version_manager.parsers[0]
        assert vp.version == Version("1.2.3")

        assert version_manager.master_version == Version("1.2.3")

    def test_bump(self):
        folder = os.path.abspath(os.path.dirname(__file__))
        tr = TaskRunner(os.path.join(folder, "fixtures/yabs_1.yaml"))
        version_manager = tr.version_manager

        # Bump "1.2.3":
        v = version_manager.bump("patch", calc_only=True)
        assert v == Version("1.2.4")

        with pytest.raises(RuntimeError):
            v = version_manager.bump("prerelease", calc_only=True)

        v = version_manager.bump("postrelease", calc_only=True)
        assert v == Version("1.2.4-a1")

        v = version_manager.bump(
            "postrelease",
            prerelease_prefix="rc",
            prerelease_start_idx=0,
            calc_only=True,
        )
        assert v == Version("1.2.4-rc0")

        v = version_manager.bump("minor", calc_only=True)
        assert v == Version("1.3.0")

        v = version_manager.bump("major", calc_only=True)
        assert v == Version("2.0.0")

        # Bump "1.2.3-PRE":

        v = Version("1.2.3-0")
        version_manager.set_version(v, False)

        v = version_manager.bump("patch", calc_only=True)
        assert v == Version("1.2.3")  # we are coming from a pre-release!

        v = version_manager.bump("prerelease", calc_only=True)
        assert v == Version("1.2.3-a1")  # we are coming from a pre-release!

        v = version_manager.bump("postrelease", calc_only=True)
        assert v == Version("1.2.3-a1")  # we are coming from a pre-release!

        v = version_manager.bump("minor", calc_only=True)
        assert v == Version("1.3.0")

        v = version_manager.bump("major", calc_only=True)
        assert v == Version("2.0.0")
