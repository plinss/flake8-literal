"""Checker for quote handling on string literals."""

import tokenize
from abc import abstractproperty
from typing import ClassVar, FrozenSet, Iterator, List, Optional, Sequence, Set, Tuple

from typing_extensions import Protocol


try:
	import pkg_resources
	package_version = pkg_resources.get_distribution(__package__).version
except pkg_resources.DistributionNotFound:
	package_version = 'unknown'


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


class Checker:
	"""Base class for literal checkers."""

	name: ClassVar[str] = __package__.replace('_', '-')
	version: ClassVar[str] = package_version
	plugin_name: ClassVar[str]

	tokens: Sequence[tokenize.TokenInfo]
	_docstring_tokens: Optional[FrozenSet[tokenize.TokenInfo]]

	@classmethod
	def parse_options(cls, options: Options) -> None:
		cls.plugin_name = (' (' + cls.name + ')') if (options.literal_include_name) else ''

	def __init__(self, logical_line: str, tokens: Sequence[tokenize.TokenInfo]) -> None:
		self.tokens = tokens
		self._docstring_tokens = None

	def _message(self, token: tokenize.TokenInfo, message: Message, **kwargs) -> Tuple[Tuple[int, int], str]:
		return (token.start, f'{message.code}{self.plugin_name} {message.text(**kwargs)}')

	@property
	def docstring_tokens(self) -> FrozenSet[tokenize.TokenInfo]:
		"""Find docstring tokens, which are initial strings or strings immediately after class or function defs."""
		if (self._docstring_tokens is None):
			docstrings: Set[tokenize.TokenInfo] = set()
			expect_docstring = True
			expect_colon = False
			bracket_depth = 0
			for token in self.tokens:
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
			self._docstring_tokens = frozenset(docstrings)
		return self._docstring_tokens

	def _process_literals(self, tokens: Sequence[tokenize.TokenInfo]) -> Iterator[Tuple[Tuple[int, int], str]]:
		raise NotImplementedError()

	def __iter__(self) -> Iterator[Tuple[Tuple[int, int], str]]:
		"""Primary call from flake8, yield error messages."""
		continuation: List[tokenize.TokenInfo] = []
		for token in self.tokens:
			if (token.type in IGNORE_TOKENS):
				continue

			if (tokenize.STRING == token.type):
				continuation.append(token)
				continue

			for message in self._process_literals(continuation):
				yield message
			continuation = []

		for message in self._process_literals(continuation):
			yield message
