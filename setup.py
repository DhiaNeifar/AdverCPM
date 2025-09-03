from setuptools import setup, find_packages
from pathlib import Path

version = {}
version_file = Path("src/advercpm/version.py")
exec(version_file.read_text(), version)

setup(
    name="AdverCPM",  # Project name
    version=version["__version__"],  # Follow semantic versioning (major.minor.patch)
    author="Dhia Neifar",
    author_email="neifar@umich.edu",
    description="Integrate Adversarial attacks on CPM datasets.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/DhiaNeifar/AdverCPM.git",  # Repo URL
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",       # or 4 - Beta, 5 - Production/Stable
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
    ],
    keywords="opencda opencood opencpm",  # For PyPI search
    packages=find_packages(where="src"),  # Auto-detect packages in src/
    package_dir={"": "src"},
    python_requires=">=3.7,<3.9",
    install_requires=["pytest"],
    extras_require={
        "dev": ["pytest", "black", "flake8", "pre-commit"],  # pip install .[dev]
        "docs": ["sphinx", "mkdocs"],
    },
    include_package_data=True,  # Uses MANIFEST.in
    entry_points={
        "console_scripts": [
            "advercpm-run=advercpm.simulation.runner:main",
        ],
    },

    project_urls={
        "Bug Tracker": "https://github.com/DhiaNeifar/AdverCPM.git",
        # "Documentation": "https://your-docs-site.com",
    },
)
