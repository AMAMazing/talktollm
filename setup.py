from setuptools import setup, find_packages
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='talktollm',
    version='0.5.3',
    author="Alex M",
    author_email="alexmalone489@gmail.com", 
    description="A Python utility for interacting with large language models (LLMs) via web automation",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/AMAMazing/talktollm",
    keywords=["llm", "automation", "gui", "pyautogui", "gemini", "deepseek", "clipboard", "aistudio"],
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'talktollm': ['images/deepseek/*', 'images/gemini/*', 'images/aistudio/*'],
    },
    install_requires=[
        'pywin32',
        'pyautogui',
        'pillow',
        'optimisewait'
    ],
    entry_points={
        'console_scripts': [
            'talktollm=talktollm.__init__:talkto',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows", 
        "Development Status :: 4 - Beta", 
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    python_requires=">=3.6",
)
