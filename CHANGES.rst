v2.0.0 (2025-10-27)
===================

Bug Fixes
---------

- Fix parsing of TOML by upgrading to Python 3.13 and using tomllib, by Eric Larson. (#16)


Other Changes and Additions
---------------------------

- Code must now be checked out before running the action in order to ensure an up-to-date ``pyproject.toml`` is used. (#17)
