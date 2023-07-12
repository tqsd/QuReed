"""quasi installation configuration"""
import setuptools

setuptools.setup(
    name="quasi",
    version="0.0.2",
    author="Simon Sekavčnik",
    author_email="simon.sekavcnik@tum.de",
    description="Simulating quantum experiments with realistic device models",
    license="Apache 2.0",
    packages=["quasi"],
    install_requires=["numpy", "numba", "scipy"],
)
