from setuptools import setup, find_packages

setup(
    name="goose-crestron-xio",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "httpx>=0.24.0",
        "aiohttp>=3.8.0",
        "fastapi>=0.68.0",
        "pydantic>=1.8.0",
        "python-multipart>=0.0.5",
    ],
    author="Nik",
    author_email="your.email@example.com",
    description="Goose extension for managing Crestron devices through the XiO Cloud service",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/goose-crestron-xio",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)