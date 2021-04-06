import json
import os
import re
import sys
from pathlib import Path

from github import Github
from toml import loads
from towncrier._settings import parse_toml

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
print(f'Base repository is {basereponame}')
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

skip_label = cl_config.get('changelog_skip_label', None)
pr_labels = [e['name'] for e in event['pull_request']['labels']]

if skip_label and skip_label in pr_labels:
    print(f'Skipping towncrier changelog plugin because "{skip_label}" '
          'label is set')
    sys.exit(0)


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
