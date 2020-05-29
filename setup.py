"""Installation of scm-helper."""
import setuptools

with open("README.md", "r") as fh:
    DESCRIPTION = fh.read()

VERSION = {}
with open("scm_helper/version.py") as fh:
    exec(fh.read(), VERSION)

setuptools.setup(
    name="scm-helper",
    version=VERSION["VERSION"],
    author="Colin Robbins",
    author_email="colin.john.robbins@gmail.com",
    description="Helper tool to manage data in Swim Club Manager",
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/ColinRobbins/scm-helper",
    entry_points={"console_scripts": ["scm=scm_helper.main:main"]},
    project_urls={
        "Bug Tracker": "https://github.com/ColinRobbins/scm-helper/issues",
        "Documentation": "https://github.com/ColinRobbins/scm-helper/wiki",
        "Source Code": "https://github.com/ColinRobbins/scm-helper",
        "Change Log": "https://github.com/ColinRobbins/scm-helper/blob/master/CHANGELOG.md",
    },
    packages=setuptools.find_packages(),
    install_requires=[
        "schema>=0.7.2",
        "requests>=2.22.0",
        "pyyaml>=5.3",
        "cryptography>=2.8",
        "func-timeout>=4.3.5",
        "selenium>=3.141.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
