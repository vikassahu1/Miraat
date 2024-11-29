from setuptools import setup, find_packages

setup(
    name="miraat",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "uvicorn",
        "pydantic",
        "firebase-admin",
    ],
)
