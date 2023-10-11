from setuptools import setup, find_packages


setup(
    name="credentials_manager",
    version="1.0",
    author="Julian René Schambach",
    author_email="julian.schambach@student.uni-tuebingen.de",
    description="A module that allows a client to connect and communicate with a Credentials Manager Server.",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "jsonschema",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
