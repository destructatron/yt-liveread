"""Setup script for YouTube Live Chat TTS Reader"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh
        if line.strip() and not line.startswith("#") and not line.startswith("git+")
    ]

setup(
    name="yt-liveread",
    version="0.1.0",
    author="Harley",
    description="Read YouTube live chat messages aloud using text-to-speech",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yt-liveread",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "yt-liveread=yt_liveread.main:main",
        ],
    },
)
