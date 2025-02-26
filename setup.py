from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aurelis",
    version="1.0.0",
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
        "click>=8.0.0",
        "rich>=10.0.0",
        "python-dotenv>=0.19.0",
        "faiss-cpu>=1.7.0",
        "numpy>=1.19.0",
        "requests>=2.26.0",
        "aiohttp>=3.8.0",
        "duckduckgo-search>=3.0.0",
        "azure-ai-inference",
        "scipy>=1.7.0",
        "faiss-cpu",
        "pyperclip>=1.8.2",
        "pytest>=7.0.0",
        "pylint>=2.17.0",
    ],
    entry_points={
        "console_scripts": [
            "aurelis=aurelis.bin.aurelis:main",
        ],
    },
)
