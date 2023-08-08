from setuptools import setup, find_packages

setup(
    name="ldap-automation",
    version="0.1",
    packages=find_packages(),
    # install_requires=["Click", "ldap3", "oracledb"],
    install_requires=["Click", "ldap3"],
    entry_points="""
        [console_scripts]
        ldap-automation=cli:main_group
    """,
)
