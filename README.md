# GitHub Action for Towncrier Changelog

Check if a change log entry (fragment file) is present. If present, whether
it is named correctly. If not present, whether it is allowed to be missing.
Create a `.github/workflows/check_changelog_entry.yml` as follows.
Except for `GITHUB_TOKEN`, other `env` entries are optional with defaults
shown:

```yaml
name: Check PR change log

on:
  pull_request:
    types: [opened, synchronize, labeled, unlabeled]

jobs:
  changelog_checker:
    name: Check if towncrier change log entry is correct
    runs-on: ubuntu-latest
    steps:
    - uses: scientific-python/action-towncrier-changelog@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        BOT_USERNAME: changelog-bot
```

Your repository must contain a `pyproject.toml` in the root directory
with the appropriate configurations. An example showing all options is:

```
[tool.changelog-bot]
    [tool.changelog-bot.towncrier_changelog]
        enabled = true  # default is false
        verify_pr_number = true  # default is false
        changelog_skip_label = "no-changelog-entry-needed"  # default is none
        changelog_noop_label = "skip-changelog-checks"
        whatsnew_label = "whatsnew-needed"
        whatsnew_pattern = '''docs\/whatsnew\/\d+\.\d+\.rst'''

[tool.towncrier]
    package = "yourpackagename"
    filename = "CHANGES.rst"
    directory = "docs/changes"
    underlines = "=-^"
    template = "docs/changes/template.rst"

    [[tool.towncrier.type]]
        directory = "feature"
        name = "New Features"
        showcontent = true

    [[tool.towncrier.type]]
        directory = "api"
        name = "API Changes"
        showcontent = true

    [[tool.towncrier.type]]
        directory = "bugfix"
        name = "Bug Fixes"
        showcontent = true

    [[tool.towncrier.type]]
        directory = "other"
        name = "Other Changes and Additions"
        showcontent = true

    [[tool.towncrier.section]]
        name = ""
        path = ""

    [[tool.towncrier.section]]
        name = "yourpackagename.subpackage1"
        path = "subpackage1"

    [[tool.towncrier.section]]
        name = "yourpackagename.subpackage2"
        path = "subpackage2"

    [[tool.towncrier.section]]
    ...
```
