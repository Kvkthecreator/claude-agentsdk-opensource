"""
Setup.py for backward compatibility.

Modern configuration is in pyproject.toml.
This file ensures proper metadata extraction for older pip/setuptools versions.
"""

from setuptools import setup, find_packages

# Read version from __init__.py to keep in sync
def get_version():
    with open("claude_agent_sdk/__init__.py") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="claude-agent-sdk",
    version=get_version(),
    packages=find_packages(include=["claude_agent_sdk*"]),
    python_requires=">=3.10",
)
