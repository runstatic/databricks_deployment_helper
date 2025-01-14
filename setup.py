from setuptools import setup, find_packages

setup(
    name="databricks_deployment_helper",
    version="0.2",
    packages=find_packages(exclude=["tests", "tests.*"]),
    url="https://github.com/runstatic/databricks_deployment_helper",
    license="",
    author="Emanuele Viglianisi, David Hohensinn, Philip Buttinger",
    author_email="emanuele.viglianisi@runtastic.com, breaka@gmx.at, philip.buttinger@runtastic.com",  # TODO: update your email if you want
    description="A set of python classes to define databricks job",
    install_requires=[
        "pyyaml==6.0",
        "gitpython==3.1.43",
        "glom==23.3.0",
    ],
)
