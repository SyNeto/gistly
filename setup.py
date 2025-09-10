from setuptools import setup, find_packages

setup(
    name="gistly",
    version="1.0.0",
    description="CLI tool for managing GitHub Gists",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "click>=8.1.0"
    ],
    entry_points={
        'console_scripts': [
            'gist=gist_manager.cli:main',
            'quick-gist=gist_manager.cli:quick_command',
        ],
    },
    python_requires=">=3.7",
)