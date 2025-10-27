# Container image that runs your code.
# NOTE: Could speed things up if you use an existing image with all the
#       deps pre-installed but still not as fast as TypeScript.
FROM python:3.13.9

RUN python -m pip install --upgrade pip PyGithub towncrier

# Copies code file action repository to the filesystem path `/` of the container
COPY entrypoint.sh /entrypoint.sh

COPY check_changelog.py /check_changelog.py

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["/entrypoint.sh"]
