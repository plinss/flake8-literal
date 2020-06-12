#!/usr/bin/env python3
"""Unit tests."""

import os
import subprocess
import tempfile
import unittest
from typing import List


def flake8(test: str, options: List[str] = None) -> List[str]:
	"""Run flake8 on test input and return output."""
	with tempfile.NamedTemporaryFile(delete=False) as temp_file:
		temp_file.write(test.encode('utf-8'))
	# print(test)
	# print(' '.join(['flake8', '--isolated', '--select=LIT', temp_file.name] + [f'--literal-{option}' for option in (options or [])]))
	process = subprocess.Popen(['flake8', '--isolated', '--select=LIT', temp_file.name] + [f'--literal-{option}' for option in (options or [])],
	                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = process.communicate()
	os.remove(temp_file.name)
	if (stderr):
		return [f'0:0:{line}' for line in stderr.decode('utf-8').splitlines()]
	# print(repr([line.split(':', 1)[1] for line in stdout.decode('utf-8').splitlines()]))
	return [line.split(':', 1)[1] for line in stdout.decode('utf-8').splitlines()]


class TestQuotes(unittest.TestCase):
	"""Test quote handling."""

	def test_valid(self) -> None:
		self.assertEqual(flake8('"""module docstring"""'), [])
		self.assertEqual(flake8('"""module docstring"""\n"""additional docstring"""'), [])
		self.assertEqual(flake8('def strings(x={1:2}, y=[({3:4},)]):\n    """function docstring"""\n    """additional function docstring'), [])
		self.assertEqual(flake8('x = 42\n"""variable docstring"""\n"""additional varaible docstring"""'), [])
		self.assertEqual(flake8('class Foo: """inline docstring""" ;'), [])
		self.assertEqual(flake8('def inline(x={1:2}, y=[({3:4},)]): """inline docstring""" ; pass'), [])

		self.assertEqual(flake8("x = '''multiline\n string'''"), [])

		self.assertEqual(flake8("x = 'inline string'"), [])

	def test_valid_switched(self) -> None:
		self.assertEqual(flake8("'''module docstring'''", ['docstring-quotes=single']), [])
		self.assertEqual(flake8("'''module docstring'''\n'''additional docstring'''", ['docstring-quotes=single']), [])
		self.assertEqual(flake8("def strings(x={1:2}, y=[({3:4},)]):\n    '''function docstring'''\n    '''additional function docstring'''",
		                        ['docstring-quotes=single']), [])
		self.assertEqual(flake8("x = 42\n'''variable docstring'''\n'''additional varaible docstring'''", ['docstring-quotes=single']), [])
		self.assertEqual(flake8("class Foo: '''inline docstring''' ;'", ['docstring-quotes=single']), [])
		self.assertEqual(flake8("def inline(x={1:2}, y=[({3:4},)]): '''inline docstring''' ; pass", ['docstring-quotes=single']), [])

		self.assertEqual(flake8('x = """multiline\n string"""', ['multiline-quotes=double']), [])

		self.assertEqual(flake8('x = "inline string"', ['inline-quotes=double']), [])

	def test_wrong_quote(self) -> None:
		self.assertEqual(flake8("'''module docstring'''"), [
			'1:1: LIT006 Use double quotes for docstring',
		])
		self.assertEqual(flake8("'''module docstring'''\n'''additional docstring'''"), [
			'1:1: LIT006 Use double quotes for docstring',
			'2:1: LIT006 Use double quotes for docstring',
		])
		self.assertEqual(flake8('x = """multiline\n string"""'), [
			'1:5: LIT003 Use single quotes for multiline string',
		])
		self.assertEqual(flake8('x = "inline string"'), [
			'1:5: LIT001 Use single quotes for string',
		])
		self.assertEqual(flake8('x = "inline string with \'both\' \\\"quotes\\\""'), [
			'1:5: LIT001 Use single quotes for string',
		])
		self.assertEqual(flake8(r'x = r"\raw\string"'), [
			'1:5: LIT001 Use single quotes for string',
		])

	def test_wrong_quote_switched(self) -> None:
		self.assertEqual(flake8('"""module docstring"""', ['docstring-quotes=single']), [
			'1:1: LIT005 Use single quotes for docstring',
		])
		self.assertEqual(flake8('"""module docstring"""\n"""additional docstring"""', ['docstring-quotes=single']), [
			'1:1: LIT005 Use single quotes for docstring',
			'2:1: LIT005 Use single quotes for docstring',
		])
		self.assertEqual(flake8("x = '''multiline\n string'''", ['multiline-quotes=double']), [
			'1:5: LIT004 Use double quotes for multiline string',
		])
		self.assertEqual(flake8("x = 'inline string'", ['inline-quotes=double']), [
			'1:5: LIT002 Use double quotes for string',
		])
		self.assertEqual(flake8('x = \'inline string with \\\'both\\\' "quotes"\'', ['inline-quotes=double']), [
			'1:5: LIT002 Use double quotes for string',
		])
		self.assertEqual(flake8(r"x = r'\raw\string'", ['inline-quotes=double']), [
			'1:5: LIT002 Use double quotes for string',
		])

	def test_non_triple(self) -> None:
		self.assertEqual(flake8('"module docstring"'), [
			'1:1: LIT008 Use triple double quotes for docstring',
		])
		self.assertEqual(flake8("'module docstring'", ['docstring-quotes=single']), [
			'1:1: LIT007 Use triple single quotes for docstring',
		])
		self.assertEqual(flake8("'module docstring'"), [
			'1:1: LIT006 Use double quotes for docstring',
		])
		self.assertEqual(flake8('"module docstring"', ['docstring-quotes=single']), [
			'1:1: LIT005 Use single quotes for docstring',
		])

	def test_avoid_escape(self) -> None:
		self.assertEqual(flake8("x = 'avoid \\\' escape'"), [  # noqa: LIT013
			'1:5: LIT011 Use double quotes for string to avoid escaped single quote',
		])
		self.assertEqual(flake8('x = "avoid \\\" escape"', ['inline-quotes=double']), [  # noqa: LIT014
			'1:5: LIT012 Use single quotes for string to avoid escaped double quote',
		])


class TestEscapes(unittest.TestCase):
	"""Test escape handling."""

	def test_valid(self) -> None:
		self.assertEqual(flake8('x = \'inline string with "quotes"\''), [])
		self.assertEqual(flake8('x = \'inline string with \\\'both\\\' "quotes"\''), [])
		self.assertEqual(flake8('x = "avoid \' escape"'), [])

	def test_valid_switched(self) -> None:
		self.assertEqual(flake8('x = "inline string with \'quotes\'"', ['inline-quotes=double']), [])
		self.assertEqual(flake8('x = "inline string with \\\"both\\\" \'quotes\'"', ['inline-quotes=double']), [])
		self.assertEqual(flake8('x = \'avoid " escape\'', ['inline-quotes=double']), [])

	def test_bad_escape(self) -> None:
		self.assertEqual(flake8('x = "avoid \\\' escape"'), [
			'1:5: LIT013 Escaped single quote is not necessary',
		])
		self.assertEqual(flake8('x = "avoid \\\' escape"', ['inline-quotes=double']), [
			'1:5: LIT013 Escaped single quote is not necessary',
		])
		self.assertEqual(flake8('x = \'avoid \\\" escape\''), [
			'1:5: LIT014 Escaped double quote is not necessary',
		])
		self.assertEqual(flake8('x = \'avoid \\\" escape\'', ['inline-quotes=double']), [
			'1:5: LIT014 Escaped double quote is not necessary',
		])


class TestContinuation(unittest.TestCase):
	"""Test continuation string handling."""

	def test_valid(self) -> None:
		self.assertEqual(flake8("x = 'first' 'inline string'"), [])
		self.assertEqual(flake8('x = "first" "avoid \' escape"'), [])
		self.assertEqual(flake8('x = \'first " escape\' "avoid \' escape"'), [])

	def test_valid_switched(self) -> None:
		self.assertEqual(flake8('x = "first" "inline string"', ['inline-quotes=double']), [])
		self.assertEqual(flake8('x = \'first\' \'avoid " escape\'', ['inline-quotes=double']), [])
		self.assertEqual(flake8('x = "first \' escape" \'avoid " escape\'', ['inline-quotes=double']), [])

	def test_continuation(self) -> None:
		self.assertEqual(flake8('x = \'first\' "second"'), [
			'1:13: LIT001 Use single quotes for string',
		])
		self.assertEqual(flake8('x = \'first\' "second"', ['inline-quotes=double']), [
			'1:5: LIT002 Use double quotes for string',
		])
		self.assertEqual(flake8('x = \'first\' "avoid \' escape"'), [
			'1:5: LIT015 Use double quotes for continuation strings to match',
		])
		self.assertEqual(flake8('x = "first" \'avoid " escape\'', ['inline-quotes=double']), [
			'1:5: LIT016 Use single quotes for continuation strings to match',
		])
		self.assertEqual(flake8("x = 'first' 'avoid \\\' escape'"), [  # noqa: LIT013
			'1:5: LIT015 Use double quotes for continuation strings to match',
			'1:13: LIT011 Use double quotes for string to avoid escaped single quote',
		])
		self.assertEqual(flake8('x = "first" "avoid \\\" escape"', ['inline-quotes=double']), [  # noqa: LIT014
			'1:5: LIT016 Use single quotes for continuation strings to match',
			'1:13: LIT012 Use single quotes for string to avoid escaped double quote',
		])

		# XXX add "one" "tw'o" 'th"ree' - should complain about 1st


class TestRaw(unittest.TestCase):
	"""Test raw string handling."""

	def test_valid(self) -> None:
		self.assertEqual(flake8(r"x = r'\raw\string'"), [])
		self.assertEqual(flake8(r"x = 'non-raw\nstring'"), [])
		self.assertEqual(flake8(r"x = '\\non-raw\nstring'"), [])
		self.assertEqual(flake8(r"x = '\\'"), [])

	def test_valid_switched(self) -> None:
		self.assertEqual(flake8(r'x = r"\raw\string"', ['inline-quotes=double']), [])
		self.assertEqual(flake8(r'x = "non-raw\nstring"', ['inline-quotes=double']), [])
		self.assertEqual(flake8(r'x = "\\non-raw\nstring"', ['inline-quotes=double']), [])
		self.assertEqual(flake8(r'x = "\\"', ['inline-quotes=double']), [])

	def test_raw(self) -> None:
		self.assertEqual(flake8("x = r'unnecessary raw'"), [
			'1:5: LIT101 Remove raw prefix when not using escapes',
		])
		self.assertEqual(flake8(r"x = 'need \\ raw'"), [
			'1:5: LIT102 Use raw prefix to avoid escaped slash',
		])


class TestOptions(unittest.TestCase):
	"""Test options."""

	def test_no_avoid_escape(self) -> None:
		self.assertEqual(flake8('x = "avoid \' escape"', ['no-avoid-escape']), [
			'1:5: LIT001 Use single quotes for string',
		])
		self.assertEqual(flake8('x = \'first\' "avoid \' escape"', ['no-avoid-escape']), [
			'1:13: LIT001 Use single quotes for string',
		])
		self.assertEqual(flake8("x = 'avoid \\\' escape'", ['no-avoid-escape']), [])  # noqa: LIT013
		self.assertEqual(flake8("x = 'not\\raw'", ['no-avoid-escape']), [])  # noqa: LIT102
		pass

	def test_include_name(self) -> None:
		self.assertEqual(flake8('x = "inline string"', ['include-name']), [
			'1:5: LIT001 (flake8-literal) Use single quotes for string',
		])


if __name__ == '__main__':
	unittest.main()
