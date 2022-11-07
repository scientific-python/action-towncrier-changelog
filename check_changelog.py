import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

import pkg_resources
from github import Github
from toml import loads

event_name = os.environ['GITHUB_EVENT_NAME']
if not event_name.startswith('pull_request'):
    print(f'No-op for {event_name}')
    sys.exit(0)

event_jsonfile = os.environ['GITHUB_EVENT_PATH']

with open(event_jsonfile, encoding='utf-8') as fin:
    event = json.load(fin)

bot_username = os.environ.get('BOT_USERNAME', 'astropy-bot')
basereponame = event['pull_request']['base']['repo']['full_name']
g = Github(os.environ.get('GITHUB_TOKEN'))

# Grab config from upstream's default branch
print(f'Bot username: {bot_username}')
print(f'Base repository: {basereponame}')
print()
baserepo = g.get_repo(basereponame)
pyproject_toml = baserepo.get_contents('pyproject.toml')
toml_cfg = loads(pyproject_toml.decoded_content.decode('utf-8'))

try:
    cl_config = toml_cfg['tool'][bot_username]['towncrier_changelog']
except KeyError:
    print(f'Missing [tool.{bot_username}.towncrier_changelog] section.')
    sys.exit(1)

if not cl_config.get('enabled', False):
    print('Skipping towncrier changelog plugin as disabled in config')
    sys.exit(0)

# Skip check if it is one of the bots.
pr_author = event['pull_request']['user']['login']
print(f'PR author: {pr_author}')
print()
if pr_author in ('meeseeksmachine', 'pre-commit-ci[bot]'):
    print(f'Skipping towncrier changelog check for bot "{pr_author}"')
    sys.exit(0)

skip_label = cl_config.get('changelog_skip_label', None)
noop_label = cl_config.get('changelog_noop_label', 'skip-changelog-checks')
pr_labels = [e['name'] for e in event['pull_request']['labels']]

# Piggyback What's New entry check here.
whatsnew_label = cl_config.get('whatsnew_label', 'whatsnew-needed')
whatsnew_pattern = cl_config.get('whatsnew_pattern', r'docs\/whatsnew\/\d+\.\d+\.rst')

print(f'PR labels: {pr_labels}')
print()

# Really, really skip it.
if noop_label in pr_labels:
    print(f'Skipping towncrier changelog check because "{noop_label}" '
          'label is set')
    sys.exit(0)

_start_string = u".. towncrier release notes start\n"
_title_format = None
_template_fname = "towncrier:default"
_default_types = OrderedDict([
    (u"feature", {"name": u"Features", "showcontent": True}),
    (u"bugfix", {"name": u"Bugfixes", "showcontent": True}),
    (u"doc", {"name": u"Improved Documentation", "showcontent": True}),
    (u"removal", {"name": u"Deprecations and Removals", "showcontent": True}),
    (u"misc", {"name": u"Misc", "showcontent": False})])
_underlines = ["=", "-", "~"]


# This was from towncrier._settings before they changed the API to be too
# painful.
def parse_toml(config):
    if "tool" not in config:
        raise KeyError("No [tool.towncrier] section.", failing_option="all")

    config = config["tool"]["towncrier"]

    sections = OrderedDict()
    types = OrderedDict()

    if "section" in config:
        for x in config["section"]:
            sections[x.get("name", "")] = x["path"]
    else:
        sections[""] = ""

    if "type" in config:
        for x in config["type"]:
            types[x["directory"]] = {"name": x["name"],
                                     "showcontent": x["showcontent"]}
    else:
        types = _default_types

    wrap = config.get("wrap", False)

    single_file_wrong = config.get("singlefile")
    if single_file_wrong:
        raise KeyError(
            "`singlefile` is not a valid option. Did you mean `single_file`?",
            failing_option="singlefile",
        )

    single_file = config.get("single_file", True)
    if not isinstance(single_file, bool):
        raise KeyError(
            "`single_file` option must be a boolean: false or true.",
            failing_option="single_file",
        )

    all_bullets = config.get("all_bullets", True)
    if not isinstance(all_bullets, bool):
        raise KeyError(
            "`all_bullets` option must be boolean: false or true.",
            failing_option="all_bullets",
        )

    template = config.get("template", _template_fname)
    if template.startswith("towncrier:"):
        resource_name = "templates/" + template.split(
            "towncrier:", 1)[1] + ".rst"
        if not pkg_resources.resource_exists("towncrier", resource_name):
            raise KeyError(
                "Towncrier does not have a template named '%s'."
                % (template.split("towncrier:", 1)[1],)
            )

        template = pkg_resources.resource_filename("towncrier", resource_name)
    else:
        template = template

    return {
        "package": config.get("package", ""),
        "package_dir": config.get("package_dir", "."),
        "single_file": single_file,
        "filename": config.get("filename", "NEWS.rst"),
        "directory": config.get("directory"),
        "version": config.get("version"),
        "name": config.get("name"),
        "sections": sections,
        "types": types,
        "template": template,
        "start_string": config.get("start_string", _start_string),
        "title_format": config.get("title_format", _title_format),
        "issue_format": config.get("issue_format"),
        "underlines": config.get("underlines", _underlines),
        "wrap": wrap,
        "all_bullets": all_bullets,
    }


def calculate_fragment_paths(config):
    if config.get("directory"):
        base_directory = config["directory"]
        fragment_directory = None
    else:
        base_directory = os.path.join(config['package_dir'], config['package'])
        fragment_directory = "newsfragments"

    section_dirs = []
    for key, val in config['sections'].items():
        if fragment_directory is not None:
            section_dirs.append(os.path.join(base_directory, val,
                                             fragment_directory))
        else:
            section_dirs.append(os.path.join(base_directory, val))

    return section_dirs


def check_sections(filenames, sections):
    """Check that a file matches ``<section><issue number>``.
    Otherwise the root dir matches when it shouldn't.
    """
    for section in sections:
        # Make sure the path ends with a /
        if not section.endswith("/"):
            section += "/"
        pattern = section.replace("/", r"\/") + r"\d+.*"
        for fname in filenames:
            match = re.match(pattern, fname)
            if match is not None:
                return fname
    return False


config = parse_toml(toml_cfg)
pr_num = event['number']
pr = baserepo.get_pull(pr_num)
modified_files = [f.filename for f in pr.get_files()]
section_dirs = calculate_fragment_paths(config)
types = config['types'].keys()
matching_file = check_sections(modified_files, section_dirs)

# Piggyback What's New entry check here.
if whatsnew_label in pr_labels:
    whatsnew_matches = re.findall(whatsnew_pattern, '|'.join(modified_files))
    n_whatsnew_matches = len(whatsnew_matches)
    if n_whatsnew_matches == 0:
        print(f'"{whatsnew_label}" present but no What\'s New entry; please add one.')
        sys.exit(1)
    elif n_whatsnew_matches > 1:
        print(f'Too many What\'s New entries found: {whatsnew_matches}')
        sys.exit(1)
    else:
        print(f'"{whatsnew_label}" present and {whatsnew_matches[0]} is modified: OK')
else:
    print(f'No "{whatsnew_label}" label, skipping What\'s New entry check')

if skip_label and skip_label in pr_labels:
    if matching_file:
        print(f'Changelog exists when "{skip_label}" label is set')
        sys.exit(1)
    else:
        print(f'Skipping towncrier changelog check because "{skip_label}" '
              'label is set')
        sys.exit(0)

if not matching_file:
    print('No changelog file was added in the correct directories for '
          f'PR {pr_num}')
    sys.exit(1)


def check_changelog_type(types, matching_file):
    filename = Path(matching_file).name
    components = filename.split(".")
    return components[1] in types


if not check_changelog_type(types, matching_file):
    print(f'The changelog file that was added for PR {pr_num} is not '
          f'one of the configured types: {types}')
    sys.exit(1)


# TODO: Make this a regex to check that the number is in the right place etc.
if (cl_config.get('verify_pr_number', False) and
        str(pr_num) not in matching_file):
    print(f'The number in the changelog file ({matching_file}) does not '
          f'match this pull request number ({pr_num}).')
    sys.exit(1)

# Success!
print(f'Changelog file ({matching_file}) correctly added for PR {pr_num}.')
