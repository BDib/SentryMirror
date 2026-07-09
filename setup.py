from setuptools import setup, find_packages

import os

def get_version():
    about = {}
    with open(os.path.join("src", "sentry_mirror", "__about__.py")) as f:
        exec(f.read(), about)
    return about["__version__"]

setup(
    name="sentry-mirror",
    python_requires=">=3.11",
    version=get_version(),
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "aiohttp>=3.10.0",
        "aiosqlite>=0.20.0",
        "beautifulsoup4>=4.12.0",
        "fastapi>=0.110.0",
        "jsbeautifier>=2.0.0",
        "lxml>=5.0.0",
        "playwright>=1.40.0",
        "python-wappalyzer>=0.3.0",
        "requests>=2.31.0",
        "secure>=2.0.0",
        "uvicorn>=0.30.0",
        "PySide6>=6.6.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "sentry-mirror=sentry_mirror.cli:main",
        ],
    },
)
