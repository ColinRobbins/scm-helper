import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scm",
    version="1.0",
    author="Colin Robbins",
    author_email="colin.john.robbins@gmail.com",
    description="Helper tool to manage data in Swim Club Manager",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ColinRobbins/scm-helper",
    entry_points = {
        'console_scripts': ["scm=scm_helper.scm:main"]
    },
    project_urls={
        "Bug Tracker": "https://github.com/ColinRobbins/scm-helper/issues",
        "Documentation": "https://github.com/ColinRobbins/scm-helper/wiki",
        "Source Code": "https://github.com/ColinRobbins/scm-helper",
    },
    packages=setuptools.find_packages(),
    install_requires=[
      'schema',
      'requests'
    ],
classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
