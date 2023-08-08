from setuptools import setup

setup(
    name="ldap-automation",
    version="0.1",
    py_modules=["cli"],
    # install_requires=["Click", "ldap3", "oracledb"],
    install_requires=["Click", "ldap3"],
    entry_points="""
        [console_scripts]
        ldap-automation=cli:cli
    """,
)
