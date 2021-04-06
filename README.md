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
    - uses: pllim/actions-towncrier-changelog@main
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        BOT_USERNAME: astropy-bot
```

Your repository must contain a `pyproject.toml` in the root directory
with the appropriate configurations. A partial example as follows:

```
[tool.astropy-bot]
    [tool.astropy-bot.towncrier_changelog]
        enabled = true
        verify_pr_number = true
        changelog_skip_label = "no-changelog-entry-needed"

[tool.towncrier]
    package = "astropy"
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
        name = "astropy.config"
        path = "config"

    [[tool.towncrier.section]]
        name = "astropy.constants"
        path = "constants"

    [[tool.towncrier.section]]
    ...
```