from setuptools import setup
import platform

reqs=["mutagen>=1.2"]
# use avahi if available
try:
    import avahi
except ImportError:
    reqs.append("pybonjour>=1.1")

setup(
    name="spydaap",
    version="0.1dev",
    install_requires=reqs,
    entry_points={
        'console_scripts': [
            'spydaap=spydaap.cli:main'
        ]
    },
    py_modules=["spydaap.cache",
                "spydaap.cli",
                "spydaap.containers",
                "spydaap.daap_data",
                "spydaap.daap",
                "spydaap.metadata",
                "spydaap.playlists",
                "spydaap.server",
                "spydaap.zeroconf",
                "spydaap.parser.avi",
                "spydaap.parser.flac",
                "spydaap.parser.mov",
                "spydaap.parser.mp3",
                "spydaap.parser.ogg",
                "spydaap.parser.vorbis"])
