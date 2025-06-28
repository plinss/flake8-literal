"""Checker for quote handling on string literals."""

from __future__ import annotations

import tokenize
from abc import abstractproperty
from collections import deque
from tokenize import TokenInfo
from typing import ClassVar, Protocol, TYPE_CHECKING, Tuple, TypeVar

if (TYPE_CHECKING):
	import ast
	from collections.abc import Iterator, Sequence


try:
	from importlib.metadata import version
	package_version = version(__package__)
except Exception:
	package_version = 'unknown'


OptionalType = TypeVar('OptionalType')


def not_none(value: (OptionalType | None)) -> OptionalType:
	"""Strip None from type."""
	assert (value is not None)  # noqa: S101
	return value


IGNORE_TOKENS = frozenset((
	tokenize.ENCODING,
	tokenize.NEWLINE,
	tokenize.INDENT,
	tokenize.DEDENT,
	tokenize.NL,
	tokenize.COMMENT,
))

OPEN_BRACKET = frozenset(('(', '[', '{'))
CLOSE_BRACKET = frozenset((')', ']', '}'))


class Options(Protocol):
	"""Protocol for options."""

	literal_include_name: bool


class Message(Protocol):
	"""Messages."""

	@abstractproperty
	def code(self) -> str:
		...

	def text(self, **kwargs) -> str:
		...


LogicalResult = Tuple[Tuple[int, int], str]  # (line, column), text
PhysicalResult = Tuple[int, str]  # (column, text)
ASTResult = Tuple[int, int, str, type]  # (line, column, text, type)


class Checker:
	"""Base class for checkers."""

	name: ClassVar[str] = __package__.replace('_', '-')
	version: ClassVar[str] = package_version
	plugin_name: ClassVar[str]

	@classmethod
	def parse_options(cls, options: Options) -> None:
		cls.plugin_name = (' (' + cls.name + ')') if (options.literal_include_name) else ''

	def _logical_token_message(self, token: TokenInfo, message: Message, **kwargs) -> LogicalResult:
		return (token.start, f'{message.code}{self.plugin_name} {message.text(**kwargs)}')

	def _pyhsical_token_message(self, token: TokenInfo, message: Message, **kwargs) -> PhysicalResult:
		return (token.start[1], f'{message.code}{self.plugin_name} {message.text(**kwargs)}')

	def _ast_token_message(self, token: TokenInfo, message: Message, **kwargs) -> ASTResult:
		return (token.start[0], token.start[1], f'{message.code}{self.plugin_name} {message.text(**kwargs)}', type(self))

	def _ast_node_message(self, node: (ast.stmt | ast.expr), message: Message, **kwargs) -> ASTResult:
		return (node.lineno, node.col_offset, f'{message.code}{self.plugin_name} {message.text(**kwargs)}', type(self))


class Tokens:
	"""Collection of tokens that allows peeking."""

	_tokens: deque[TokenInfo]

	def __init__(self, tokens: Sequence[TokenInfo]) -> None:
		self._tokens = deque(tokens)

	def __bool__(self) -> bool:
		return bool(self._tokens)

	def __len__(self) -> int:
		return len(self._tokens)

	def _skip_ignored(self) -> None:
		while (self._tokens and (self._tokens[0].type in IGNORE_TOKENS)):
			self._tokens.popleft()

	def peek(self) -> (TokenInfo | None):
		self._skip_ignored()
		return (self._tokens[0] if (self._tokens) else None)

	def next(self) -> (TokenInfo | None):
		self._skip_ignored()
		return (self._tokens.popleft() if (self._tokens) else None)


class LiteralChecker(Checker):
	"""Base class for literal checkers."""

	tokens: Tokens
	docstring_tokens: frozenset[TokenInfo]

	def __init__(self, logical_line: str, tokens: Sequence[TokenInfo]) -> None:
		self.tokens = Tokens(tokens)
		self.docstring_tokens = self._find_docstrings(tokens)

	def _find_docstrings(self, tokens: Sequence[TokenInfo]) -> frozenset[TokenInfo]:
		"""Find docstring tokens, which are initial strings or strings immediately after class or function defs."""
		docstrings: set[TokenInfo] = set()
		expect_docstring = True
		expect_colon = False
		bracket_depth = 0
		for token in tokens:
			if (token.type in IGNORE_TOKENS):
				continue

			if (tokenize.STRING == token.type):
				if (expect_docstring):
					docstrings.add(token)
			else:
				expect_docstring = False
				if ((tokenize.NAME == token.type) and (token.string in ('class', 'def'))):
					expect_colon = True
					bracket_depth = 0
				elif (tokenize.OP == token.type):
					if (':' == token.string):
						if (0 == bracket_depth):
							if (expect_colon):
								expect_docstring = True
							expect_colon = False
					elif (token.string in OPEN_BRACKET):
						bracket_depth += 1
					elif (token.string in CLOSE_BRACKET):
						bracket_depth -= 1
		return frozenset(docstrings)

	def _process_literals(self, tokens: Sequence[TokenInfo]) -> Iterator[LogicalResult]:
		raise NotImplementedError()

	def _iter_string_continuations(self) -> Iterator[Sequence[TokenInfo]]:
		contunuation: list[TokenInfo] = []
		token = self.tokens.peek()
		fstring = None
		while (token is not None):
			if ((fstring is None) and (token.type in {tokenize.FSTRING_MIDDLE, tokenize.FSTRING_END})):
				break

			token = not_none(self.tokens.next())
			if (tokenize.STRING == token.type):
				contunuation.append(token)
				token = self.tokens.peek()
				continue

			if (tokenize.FSTRING_START == token.type):
				fstring = TokenInfo(tokenize.STRING, token.string, token.start, token.end, token.line)

				yield from self._iter_string_continuations()

				token = self.tokens.peek()
				continue
			if (tokenize.FSTRING_MIDDLE == token.type):
				fstring = TokenInfo(tokenize.STRING, (not_none(fstring).string + token.string), not_none(fstring).start, token.end, token.line)

				yield from self._iter_string_continuations()

				token = self.tokens.peek()
				continue
			if (tokenize.FSTRING_END == token.type):
				fstring = TokenInfo(tokenize.STRING, (not_none(fstring).string + token.string), not_none(fstring).start, token.end, token.line)
				contunuation.append(fstring)
				fstring = None

				token = self.tokens.peek()
				continue

			if (contunuation):
				yield contunuation
				contunuation = []

			token = self.tokens.peek()

		if (contunuation):
			yield contunuation

	def __iter__(self) -> Iterator[LogicalResult]:
		"""Primary call from flake8, yield error messages."""
		for group in self._iter_string_continuations():
			for message in self._process_literals(group):
				yield message
