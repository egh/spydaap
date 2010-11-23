==========================================
 spydaap: a simple DAAP server for python
==========================================

Requirements
------------

1. python2.4 or later
2. mutagen <http://www.sacredchao.net/quodlibet/wiki/Development/Mutagen>
3. pybonjour <http://o2s.csail.mit.edu/o2s-wiki/pybonjour> or
   python-avahi

Installing
----------

Ubuntu/Debian
~~~~~~~~~~~~~

::

  $ sudo apt-get install python-mutagen python-avahi
  $ cd spydaap
  $ sudo python setup.py install

Mac OS X
~~~~~~~~

spydaap requires a version of Python later than 2.3. If you are
running Mac OS 10.4 or earlier, you will need to install a more recent
version of Python and setuptools.

::

  $ cd spydaap
  $ sudo python setup.py install

Running
-------

::

  $ spydaap

``~/Music/`` is the default directory where spydaap looks for media
files. It can be change by editing ``~/spydaap/config.py`` (see
``config.py.example``)

Customizing
-----------

See ``config.py.example`` for information on setting port, name,
etc. There also examples of some custom smart playlists. For writing
your own smart playlists, see ``spydaap/playlists.py``.
