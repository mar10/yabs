# -*- coding: utf-8 -*-
# (c) 2020-2021 Martin Wendt and contributors; see https://github.com/mar10/yabs
# Licensed under the MIT license: https://www.opensource.org/licenses/mit-license.php
"""
"""
import pytest

from yabs.util import (
    assert_always,
    check_arg,
    format_elap,
    format_rate,
    get_dict_attr,
    shorten_string,
)


class TestBasics:
    def test_assert(self):
        assert_always(1)
        assert_always(1, "test")
        with pytest.raises(AssertionError):
            assert_always(0)
        with pytest.raises(AssertionError, match=".*foobar.*"):
            assert_always(0, "foobar")

    def test_check_arg(self):
        def foo(name, amount, options=None):
            check_arg(name, str)
            check_arg(amount, (int, float), amount > 0)
            check_arg(options, dict, or_none=True)
            return name

        assert foo("x", 10) == "x"
        assert foo("x", 10, {1: 2}) == "x"
        with pytest.raises(TypeError, match=".*but got <class 'int'>.*"):
            foo("x", 10, 42)
        with pytest.raises(ValueError, match=".*Invalid argument value.*"):
            foo("x", -10)
        return

    def test_get_attr(self):

        # next_
        class TestClass:  # noqa: B903
            def __init__(self, val):
                self.val = val

        d = {
            "s1": 1,
            "s2": "foo",
            "l1": [],
            "l2": [1, 2, 3],
            "d1": {},
            "d2": {"d21": 42, "d22": {"d221": "bar"}},
            "o": TestClass("baz"),
        }
        assert get_dict_attr(d, "s1") == 1
        assert get_dict_attr(d, "l1") == []
        assert get_dict_attr(d, "l2") == [1, 2, 3]
        assert get_dict_attr(d, "l2.[1]") == 2
        assert get_dict_attr(d, "d1") == {}
        assert get_dict_attr(d, "d2.d21") == 42
        assert get_dict_attr(d, "d2.d22.d221") == "bar"
        assert get_dict_attr(d, "o.val") == "baz"

        with pytest.raises(KeyError):
            get_dict_attr(d, "foobar")
        with pytest.raises(
            AttributeError, match=r".*object has no attribute 'foobar'.*"
        ):
            get_dict_attr(d, "s1.foobar")
        with pytest.raises(ValueError, match=r".*Use `\[INT\]` syntax.*"):
            get_dict_attr(d, "l2.foobar")
        with pytest.raises(IndexError):
            get_dict_attr(d, "l2.[99]")
        with pytest.raises(KeyError):
            get_dict_attr(d, "d1.foobar")

        # Defaults:
        assert get_dict_attr(d, "foobar", "def") == "def"
        assert get_dict_attr(d, "s1.foobar", "def") == "def"
        assert get_dict_attr(d, "l2.foobar", "def") == "def"
        assert get_dict_attr(d, "l2.[99]", "def") == "def"
        assert get_dict_attr(d, "foobar", "def") == "def"
        assert get_dict_attr(d, "d1.foobar", "def") == "def"

    def test_shorten_string(self):
        s = (
            "Do you see any Teletubbies in here?"
            "Do you see a slender plastic tag clipped to my shirt with my name printed on it?"
        )
        assert shorten_string(None, 10) is None
        assert len(shorten_string(s, 20)) == 20
        assert len(shorten_string(s, 20, min_tail_chars=7)) == 20
        assert shorten_string(s, 20) == "Do you see any [...]"
        assert shorten_string(s, 20, min_tail_chars=7) == "Do you s[...] on it?"

    def test_format_elap(self):
        assert format_elap(1.23456) == "1.23 sec"
        assert format_elap(1.23456, high_prec=True) == "1.235 sec"
        assert format_elap(3677) == "1:01:17 hrs"
        assert format_elap(367) == "6:07 min"
        assert format_elap(367, high_prec=True) == "6:07.00 min"
        assert format_elap(12.34, count=10) == "12.3 sec, 0.8 items/sec"

    def test_format_rate(self):
        assert format_rate(0, 0) == "0"
        assert format_rate(0, None) == "0"
        assert format_rate(None, 0) == "0"
        assert format_rate(12345, 0) == "0"
        assert format_rate(12345, 10.0) == "1234"
        assert format_rate(12345, 100.0) == "123.5"
        assert format_rate(12345, 1000.0) == "12.35"
        assert format_rate(12345, 10000.0) == "1.234"
        assert format_rate(12345, 100000.0) == "0.123"
        assert format_rate(12345, 1000000.0) == "0.012"

    def test_log(self):
        from snazzy import colors_enabled, enable_colors, green, red

        assert not colors_enabled()
        assert red("error") == "error"
        assert green("ok") == "ok"

        enable_colors(True, True)
        assert red("error") == "\x1b[91merror\x1b[39m"
        assert green("ok") == "\x1b[32mok\x1b[39m"
