import os

from setuptools import find_packages, setup

# Get dependencies from requirements.txt
SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(SETUP_DIR, "requirements.txt"), "r") as f:
    REQUIRED_PACKAGES = f.read().splitlines()

setup(
    name="spineq",
    version="1.0",
    description="Optimisation backend for Spatial Inequality in the Smart City",
    url="https://github.com/alan-turing-institute/spatial-inequality",
    author="Jack Roberts",
    license="MIT",
    packages=find_packages(),
    install_requires=REQUIRED_PACKAGES,
)
