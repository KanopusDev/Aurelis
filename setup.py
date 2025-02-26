from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aurelis",
    version="1.0.1",
    author="Pradyumn Tandon",
    author_email="pradyumn.tandon@hotmail.com",
    description="AI-powered coding assistant with advanced reasoning capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Kanopusdev/aurelis",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click",
        "rich",
        "python-dotenv",
        "faiss-cpu",
        "numpy",
        "requests",
        "aiohttp",
        "asyncio",
        "duckduckgo-search",
        "azure-ai-inference",
        "scipy",
        "pyperclip",
        "pytest",
        "pylint",
        "pathlib",
        "typing",
        "black",
        "isort",
        "mypy",
        "pytest-asyncio",
        "pytest-cov",
    ],
    entry_points={
        "console_scripts": [
            "aurelis=aurelis.bin.aurelis:main",
        ],
    },
)
