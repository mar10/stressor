#!/usr/bin/env python

# NOTE: isort must not chage this import order:
# isort: skip_file

import os
import re
import sys

from setuptools import find_packages, setup
from cx_Freeze import setup, Executable  # noqa re-import setup

from stressor import __version__


# Check for Windows MSI Setup
if "bdist_msi" not in sys.argv:  # or len(sys.argv) != 2:
    raise RuntimeError(
        "This setup.py variant is only for creating 'bdist_msi' targets: {}\n"
        "Example `{} bdist_msi`".format(sys.argv, sys.argv[0])
    )

org_version = __version__

# Since we included pywin32 extensions, cx_Freeze tries to create a
# version resource. This only supports the 'a.b.c[.d]' format.
# Our version has either the for '1.2.3' or '1.2.3-a1'
unsafe_version = False
major, minor, patch = org_version.split(".", 3)
major = int(major)
minor = int(minor)
if "-" in patch:
    # We have a pre-release version, e.g. '1.2.3-a1'.
    # This is presumably a post-release increment after '1.2.2' release.
    # It must NOT be converted to '1.2.3.1', since that would be *greater*
    # than '1.2.3', which is not even released yet.
    # Approach 1:
    #     We cannot guarantee that '1.2.2.1' is correct either, so for
    #     pre-releases we assume '0.0.0.0':
    # major = minor = patch = alpha = 0
    # Approach 2:
    #     '1.2.3-a1' was presumably a post-release increment after '1.2.2',
    #     so assume '1.2.2.1':
    patch, alpha = patch.split("-", 1)
    patch = int(patch)
    # Remove leading letters
    alpha = re.sub("^[a-zA-Z]+", "", alpha)
    alpha = int(alpha)
    if unsafe_version and patch >= 1:
        patch -= 1  # 1.2.3-a1 => 1.2.2.1
    else:
        # may be 1.2.0-a1 or 2.0.0-a1: we don't know what the previous release was
        major = minor = patch = alpha = 0
else:
    patch = int(patch)
    alpha = 0

version = f"{major}.{minor}.{patch}.{alpha}"
print(f"Version {org_version}, using {version}")

try:
    readme = open("README.md", "rt").read()
except IOError:
    readme = "(readme not found. Running from tox/setup.py test?)"

# NOTE: Only need to list requirements that are not discoverable by scanning
#       the main package. For example due to dynamic or optional imports.
# Also, cx_Freeze may have difficulties with packages listed here, e.g. PyYAML:
#    https://github.com/marcelotduarte/cx_Freeze/issues/1541
install_requires = []
setup_requires = install_requires
tests_require = []

executables = [
    Executable(
        script="stressor/stressor_cli.py",
        base=None,
        target_name="stressor.exe",
        icon="docs/logo.ico",
        shortcut_name="stressor",
        copyright="(c) 2020-2024 Martin Wendt",
    )
]

# See https://cx-freeze.readthedocs.io/en/latest/distutils.html#build-exe
build_exe_options = {
    # "init_script": "Console",
    "includes": install_requires,
    # "packages": ["keyring.backends"],  # loaded dynamically
    "excludes": [
        "tkinter",
    ],
    "constants": "BUILD_COPYRIGHT='(c) 2020-2024 Martin Wendt'",
    "include_msvcr": True,
}

# See https://cx-freeze.readthedocs.io/en/latest/distutils.html#bdist-msi
bdist_msi_options = {
    "upgrade_code": "{3DA14E9B-1D2A-4D90-92D0-2375CF66AC3D}",
    "add_to_path": True,
    # "all_users": True,
    # "install_icon": "docs/logo.ico",
}

packages = find_packages(exclude=["test"])

setup(
    name="stressor",
    version=version,
    author="Martin Wendt",
    author_email="stressor@wwwendt.de",
    # copyright="(c) 2020-2024 Martin Wendt",
    maintainer="Martin Wendt",
    maintainer_email="stressor@wwwendt.de",
    url="https://github.com/mar10/stressor",
    description="Stress-test your web app.",
    long_description=readme,
    long_description_content_type="text/markdown",
    # Not required for this build-only setup config:
    classifiers=[],
    keywords="web server load test stress",
    license="The MIT License",
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    packages=packages,
    package_data={
        # If any package contains *.txt files, include them:
        # "": ["*.css", "*.html", "*.ico", "*.js"],
        "": ["*.tmpl"],
        "stressor.monitor": ["htdocs/*.*"],
    },
    zip_safe=False,
    extras_require={},
    # cmdclass={"test": ToxCommand, "sphinx": SphinxCommand},
    entry_points={"console_scripts": ["stressor = stressor.stressor_cli:run"]},
    executables=executables,
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
)
