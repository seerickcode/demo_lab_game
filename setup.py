from setuptools import setup, find_packages

setup(
    name="gamebot",
    version="0.0.1",
    license="proprietary",
    description="Demo Game Bot",
    author="Richard Clark",
    author_email="rick@seerickcode.com",
    url="https://seerickcode.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
