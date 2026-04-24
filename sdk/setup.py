"""
Setup para o KEEPIT SDK Python.

Instalação:
    pip install .
    # ou direto do GitHub:
    pip install git+https://github.com/thiagofreitas299-stack/keepit-oasis.git#subdirectory=sdk
"""

from setuptools import setup, find_packages

setup(
    name="keepit-sdk",
    version="1.0.0",
    description="SDK Python para o ecossistema KEEPIT — registre seu agente em 3 linhas",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="KEEPIT",
    author_email="dev@keepithub.com",
    url="https://keepithub.com",
    py_modules=["keepit_sdk"],
    python_requires=">=3.6",
    install_requires=[],  # zero dependências externas
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="keepit agent ai identity did blockchain",
)
