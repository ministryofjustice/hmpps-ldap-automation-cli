# Quick start guide

## Environment variables

Variables are picked up from the environment, or can be specified in a `.env` file in the current directory (at the same
level as the file `setup.py`)
See `cli/config.py` for a list of variables.

## Installation for development purposes

`python3 -m venv venv`

`source venv/bin/activate`

`pip install -r requirements.txt`

`pip install -e .`

## Installation for consuming the package

`pip install git+https://github.com/ministryofjustice/hmpps-ldap-automation-cli.git`

Optionally append `@<commit hash>`, `@<branch name>` or
`@<tag/release version>` to the end of the url to install a specific
commit

## Usage

`ldap-automation --help`

# Dev

## pre-commit

This project uses pre-commit to run a number of checks on the code before it is committed. To install the pre-commit
hooks run:

`pre-commit install`

