from setuptools import setup, find_packages
from pathlib import Path

# Read README.md with UTF-8 encoding
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="tukuy",
    version='0.0.3',
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4>=4.9.0",
        "python-slugify>=4.0.0",
    ],
    author="Juan Denis",
    author_email="juan@vene.co",
    description="A flexible data transformation library with a plugin system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jhd3197/tukuy",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", 
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)