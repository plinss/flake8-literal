"""Checker for raw string literals."""

import enum
import tokenize
from typing import ClassVar, Iterator, NamedTuple, Optional, Sequence, Tuple

from flake8.options.manager import OptionManager

import flake8_literal

from . import checker


class Message(enum.Enum):
	"""Messages."""

	UNNECESSARY_RAW = (1, 'Remove raw prefix when not using escapes')
	USE_RAW_PREFIX = (2, 'Use raw prefix to avoid escaped slash')

	@property
	def code(self) -> str:
		return (flake8_literal.raw_checker_prefix + str(self.value[0]).rjust(6 - len(flake8_literal.raw_checker_prefix), '0'))

	def text(self, **kwargs) -> str:
		return self.value[1].format(**kwargs)


class RegexRaw(enum.Enum):
	"""Raw regex type option enum."""

	AVOID = 'avoid'
	ALLOW = 'allow'
	ALWAYS = 'always'

	@classmethod
	def from_str(cls, value: str) -> Optional['RegexRaw']:
		for member in cls.__members__.values():
			if (value.lower() == member.value):
				return member
		return None


class Options(checker.Options):
	"""Protocol for options."""

	literal_re_raw: str
	literal_avoid_escape: bool


class Config(NamedTuple):
	"""Config options."""

	re_raw: RegexRaw
	avoid_escape: bool


class RawChecker(checker.Checker):
	"""Check string literals for proper raw usage."""

	config: ClassVar[Config]

	@classmethod
	def add_options(cls, option_manager: OptionManager) -> None:
		option_manager.add_option('--literal-regex-raw', default='allow',
		                          action='store', parse_from_config=True,
		                          choices=('avoid', 'allow', 'always'), dest='literal_re_raw',
		                          help='Use raw strings for regular expressions (default:allow)')

	@classmethod
	def parse_options(cls, options: Options) -> None:  # type: ignore[override]
		super().parse_options(options)
		cls.config = Config(re_raw=RegexRaw.from_str(options.literal_re_raw) or RegexRaw.ALLOW,
		                    avoid_escape=options.literal_avoid_escape)

	def _process_literals(self, tokens: Sequence[tokenize.TokenInfo]) -> Iterator[Tuple[Tuple[int, int], str]]:
		if (not tokens):
			return

		for token in tokens:
			quote = token.string[-1]
			prefix = token.string[:token.string.index(quote)].lower()
			string = token.string[len(prefix):]

			if (token in self.docstring_tokens):  # docstring
				continue

			if (string[0:3] == (quote * 3)):  # multiline
				contents = string[3:-3]
			else:  # inline
				contents = string[1:-1]

			if (('r' in prefix) and not ('\\' in contents)):
				yield self._message(token, Message.UNNECESSARY_RAW)
			if (('r' not in prefix) and (r'\\' in contents) and ('\\' not in contents.replace(r'\\', '')) and self.config.avoid_escape):
				trail_count = 0
				test_contents = contents
				while test_contents.endswith(r'\\'):
					test_contents = test_contents[:-2]
					trail_count += 1
				if (0 == (trail_count % 2)):  # raw strings can't end in an odd number of backslashes
					yield self._message(token, Message.USE_RAW_PREFIX)
