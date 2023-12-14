"""quasi installation configuration"""
from setuptools import find_packages, setup


setup(
    name="quasi",
    version="0.0.2",
    author="Simon Sekavčnik",
    author_email="simon.sekavcnik@tum.de",
    description="Simulating quantum experiments with realistic device models",
    license="Apache 2.0",
    packages=find_packages(where="."),
    install_requires=["numpy", "numba", "scipy"],
)
