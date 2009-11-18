#!/usr/bin/env python
#Copyright (C) 2008 Erik Hetzner

#This file is part of Spydaap. Spydaap is free software: you can
#redistribute it and/or modify it under the terms of the GNU General
#Public License as published by the Free Software Foundation, either
#version 3 of the License, or (at your option) any later version.

#Spydaap is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Spydaap. If not, see <http://www.gnu.org/licenses/>.

import BaseHTTPServer, SocketServer, os, signal, logging
import spydaap.daap, spydaap.metadata, spydaap.containers, spydaap.cache, spydaap.server, spydaap.zeroconf
from spydaap.daap import do
import config

logging.basicConfig()
log = logging.getLogger('spydaap')

cache = spydaap.cache.Cache(spydaap.cache_dir)
md_cache = spydaap.metadata.MetadataCache(os.path.join(spydaap.cache_dir, "media"), spydaap.parsers)
container_cache = spydaap.containers.ContainerCache(os.path.join(spydaap.cache_dir, "containers"), spydaap.container_list)
keep_running = True

def rebuild_cache(signum=None, frame=None):
    md_cache.build(spydaap.media_path)
    container_cache.clean()
    container_cache.build(md_cache)
    cache.clean()

def shutdown(signum, frame):
    keep_running = False

class MyThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    rebuild_cache()

    signal.signal(signal.SIGHUP, rebuild_cache)
    #signal.signal(signal.SIGTERM, shutdown)
    #signal.signal(signal.SIGINT, shutdown)

    zeroconf = spydaap.zeroconf.Zeroconf(spydaap.server_name,
                                         spydaap.port,  
                                         stype="_daap._tcp")
    zeroconf.publish()

    #try:
    log.warning("Listening.")
    httpd = MyThreadedHTTPServer(('0.0.0.0', spydaap.port), 
                                 spydaap.server.makeDAAPHandlerClass(spydaap.server_name, cache, md_cache, container_cache))
    while keep_running:
        httpd.serve_forever()
            
    #except (KeyboardInterrupt, select.error):
    #    keep_running = False

    log.warning("Shutting down.")

    zeroconf.close()
