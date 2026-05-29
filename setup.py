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
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["photon_weave==0.1.8", "jinja2", "simpy", "mpmath"],
    package_data={
        "qureed": ["templates/*.jinja", "assets/*.png"],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "qureed=qureed.cli.main:main",
            "qureed-template=qureed.cli.main:main",
            "qureed-gui=qureed.gui.main:start",
            "qureed-execute=qureed.simulation.simulate_from_json:main",
        ],
    },
)
