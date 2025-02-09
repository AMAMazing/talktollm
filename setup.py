from setuptools import setup, find_packages

setup(
    name='talktollm',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'talktollm': ['images/*/*'],
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
)
