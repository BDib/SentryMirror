from setuptools import setup, find_packages

import os

def get_version():
    about = {}
    with open(os.path.join("src", "sentry_mirror", "__about__.py")) as f:
        exec(f.read(), about)
    return about["__version__"]

setup(
    name="sentry-mirror",
    python_requires=">=3.10",
    version=get_version(),
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "aiohttp",
        "aiosqlite",
        "beautifulsoup4",
        "fastapi",
        "jsbeautifier",
        "lxml",
        "playwright",
        "python-wappalyzer",
        "requests",
        "secure",
        "uvicorn",
        "pydantic",
        "pydantic-settings",
    ],
    entry_points={
        "console_scripts": [
            "sentry-mirror=sentry_mirror.cli:main",
        ],
    },
)
