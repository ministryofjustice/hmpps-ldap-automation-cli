from setuptools import (
    setup,
    find_packages,
)

# Read requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

standard_pkgs = [r for r in requirements if not r.startswith("git+")]
git_pkgs = [r for r in requirements if r.startswith("git+")]
formatted_git_pkgs = [f"{git_pkg.split('/')[-1].split('.git@')[0]} @ {git_pkg}" for git_pkg in git_pkgs]
all_reqs = standard_pkgs + formatted_git_pkgs

setup(
    name="ldap-automation",
    version="0.2",
    packages=find_packages(),
    install_requires=all_reqs,
    entry_points="""
        [console_scripts]
        ldap-automation=cli:main_group
    """,
)
