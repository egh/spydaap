from setuptools import setup


setup(
    name="spydaap",
    version="0.1dev",
    install_requires=[
        'pybonjour>=1.1',
        'mutagen>=1.2',
    ],
    entry_points={
        'console_scripts': [
            'spydaap=spydaap.cli:main'
        ]
    }
)
