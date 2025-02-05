from setuptools import setup, find_packages

setup(
    name='talktollm',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'pywin32',
        'pyautogui',
        'pillow',
        'webbrowser',
        'time',
        'base64',
        'io'
    ],
    entry_points={
        'console_scripts': [
            'talktollm=talktollm.cli:main',
        ],
    },
)
