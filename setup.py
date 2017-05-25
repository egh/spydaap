from setuptools import setup
import platform

reqs = ["mutagen>=1.2"]
# use avahi if available
try:
    import avahi
except ImportError:
    reqs.append("pybonjour>=1.1")

setup(
    name="spydaap",
    version="0.1dev",
    author="Erik Hetzner",
    author_email="egh@e6h.org",
    description="A simple DAAP server",
    long_description="""
=========
 spydaap
=========

Spydaap is a media server supporting the DAAP protocol (aka iTunes
sharing). It is written in Python, uses the mutagen media metadata
library, and either the Avahi or pybonjour Zeroconf implementation.

Features:

 - Runs on Unix-like systems (Linux, *BSD, Mac OS X).
 - Can stream mp3s, ogg, flac, and Quicktime videos.
 - Supports "smart" playlists written in Python.
 - Written in 100 percent Python and easily modifiable.
 - Caches almost everything for fast performance.
 - Embeddable.""",
    url="http://launchpad.net/spydaap/",
    install_requires=reqs,
    entry_points={
        'console_scripts': [
            'spydaap=spydaap.cli:main'
        ]
    },
    packages=["spydaap", "spydaap.parser"],
    classifiers=["Development Status :: 4 - Beta",
                 "License :: OSI Approved :: GNU General Public License (GPL)",
                 "Programming Language :: Python",
                 "Topic :: Multimedia :: Sound/Audio",
                 "Operating System :: POSIX",
                 "Intended Audience :: End Users/Desktop"])
