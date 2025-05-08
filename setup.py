"""qureed installation configuration"""

import os

from setuptools import find_packages, setup

current_dir = os.path.abspath(os.path.dirname(__file__))
setup(
    name="qureed",
    version="0.0.2",
    author="Simon Sekavčnik",
    author_email="simon.sekavcnik@tum.de",
    description="Simulating quantum experiments with realistic device models",
    license="Apache 2.0",
    packages=find_packages(where="."),
    install_requires=[
        "photon_weave==0.1.7",
        "jinja2",
        "simpy",
        "mpmath"
    ],
    package_data={
        "qureed": ["templates/*.jinja", "assets/*.png"],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "qureed-template=qureed.cli:main",
            "qureed-gui=qureed.gui.main:start",
            "qureed-execute=qureed.simulation.simulate_from_json:main",
        ],
    },
)
