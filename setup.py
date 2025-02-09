from setuptools import setup, find_packages

setup(
    name='talktollm',
    version='0.2.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'talktollm': ['images//*'],
    },
    install_requires=[
        'pywin32',
        'pyautogui',
        'pillow',
        'optimisewait'
    ],
    entry_points={
        'console_scripts': [
            'talktollm=talktollm:talkto',
        ],
    },
    author="Alex M",
    description="A Python utility for interacting with large language models (LLMs) through a command-line interface",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AMAMazing/talktollm",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
