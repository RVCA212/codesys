from setuptools import setup, find_packages
import os

# Read the contents of the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read version from __init__.py
with open(os.path.join("codesys", "__init__.py"), "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

setup(
    name="codesys",
    version="0.1.6",
    author="codesys",
    author_email="sean@lmsystems.ai",
    description="A Python SDK for interacting with the Claude CLI tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/RVCA212/codesys",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.8",
    install_requires=[],
    keywords="claude, ai, language model, cli, sdk",
)