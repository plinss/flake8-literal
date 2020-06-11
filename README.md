[flake8-literal](https://github.com/plinss/flake8-literal)
==========

flake8 plugin to validate string literals.

This plugin is used to enforce consistent styling of string literals,
it recognizes inline literals, 
multline literals,
and docstrings.
You can choose between single or double quotes for each type of string.

If the `avoid-escape` feature is on (default),
it will enforce using the opposite quote type when doing so
avoid the use of escaped quotes.

It also recognizes continuation strings 
and will enforce a consistent quote style for the entire set 
when possible.

In addition it checks the usage of raw strings,
preventing unnecessary use of raw strings, 
and using raw strings when doing so will avoid an escaped backslash.

More features coming soon.


Installation
------------

Standard python package installation:

    pip install flake8-noqa


Options
-------
`literal-inline-quotes`
: Quote to use for inline string literals, choices: single, double (default: single)

`literal-multiline-quotes`
: Quote to use for multiline string literals, choices: single, double (default: single)

`literal-docstring-quotes`
: Quote to use for docstrings, choices: single, double (default: double)

`literal-avoid-escape`
: Avoid escapes in inline string literals when possible (enabled by default)

`literal-no-avoid-escape`
: Disable escape avoidance in inline string literals

`literal-include-name`
: Include plugin name in messages

`literal-no-include-name`
: Do not include plugin name in messages (default setting)

All options may be specified on the command line with a `--` prefix,
or can be placed in your flake8 config file.


Error Codes
-----------

| Code   | Message |
|--------|---------|
| LIT001 | Use single quotes for string
| LIT002 | Use double quotes for string
| LIT003 | Use single quotes for multiline string
| LIT004 | Use double quotes for multiline string
| LIT005 | Use single quotes for docstring
| LIT006 | Use double quotes for docstring
| LIT007 | Use triple single quotes for docstring
| LIT008 | Use triple double quotes for docstring
| LIT011 | Use double quotes for string to avoid escaped single quote
| LIT012 | Use single quotes for string to avoid escaped single quote
| LIT013 | Escaped single quote is not necessary
| LIT014 | Escaped double quote is not necessary
| LIT015 | Use double quotes for continuation strings to match
| LIT016 | Use single quotes for continuation strings to match
| LIT021 | Remove raw prefix when not using escapes
| LIT022 | Use raw prefix to avoid escaped slash


Examples
--------

```
x = "value"  <-- LIT001
x = 'aren\'t escapes great?'  <-- LIT011
x = "can\'t stop escaping"  <-- LIT013
x = ('one'  <-- LIT015
     "o'clock")
x = r'no need to be raw'  <-- LIT021
x = '\\windows\\path'  <-- LIT022
```