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

import optparse

import BaseHTTPServer, SocketServer, grp, httplib, logging, os, pwd, select, signal, spydaap, sys
import spydaap.daap, spydaap.metadata, spydaap.containers, spydaap.cache, spydaap.server, spydaap.zeroconf
from spydaap.daap import do

config_file = os.path.join(spydaap.spydaap_dir, "config.py")
if os.path.isfile(config_file): execfile(config_file)

cache = spydaap.cache.Cache(spydaap.cache_dir)
md_cache = spydaap.metadata.MetadataCache(os.path.join(spydaap.cache_dir, "media"), spydaap.parsers)
container_cache = spydaap.containers.ContainerCache(os.path.join(spydaap.cache_dir, "containers"), spydaap.container_list)
keep_running = True

class Log:
    """file like for writes with auto flush after each write
    to ensure that everything is logged, even during an
    unexpected exit."""
    def __init__(self, f):
        self.f = f
    def write(self, s):
        self.f.write(s)
        self.f.flush()

class MyThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""
    timeout = 1

    def __init__(self, *args):
        BaseHTTPServer.HTTPServer.__init__(self,*args)
        self.keep_running = True

    def serve_forever(self):
        while self.keep_running:
            self.handle_request()

    def force_stop(self):
        self.keep_running = False
        self.server_close()

def rebuild_cache(signum=None, frame=None):
    md_cache.build(os.path.abspath(spydaap.media_path))
    container_cache.clean()
    container_cache.build(md_cache)
    cache.clean()

def make_shutdown(httpd):
    def _shutdown(signum, frame): 
        httpd.force_stop() 
    return _shutdown

def really_main():
    rebuild_cache()
    zeroconf = spydaap.zeroconf.Zeroconf(spydaap.server_name,
                                         spydaap.port,  
                                         stype="_daap._tcp")
    zeroconf.publish()
    httpd = MyThreadedHTTPServer(('0.0.0.0', spydaap.port), 
                                 spydaap.server.makeDAAPHandlerClass(spydaap.server_name, cache, md_cache, container_cache))
    
    signal.signal(signal.SIGTERM, make_shutdown(httpd))
    signal.signal(signal.SIGHUP, rebuild_cache)

    while httpd.keep_running:
        try:
            httpd.serve_forever()
        except select.error:
            pass
        except KeyboardInterrupt:
            httpd.force_stop()
    zeroconf.unpublish()

def main():
    daemonize = True

    def getpwname(o, s, value, parser):
        parser.values.user = pwd.getpwnam(value)[2]

    def getgrname(o, s, value, parser):
        parser.values.group = grp.getgrnam(value)[2]

    parser = optparse.OptionParser()

    parser.add_option("-f", "--foreground", action="store_false",
                      dest="daemonize", default=True,
                      help="run in foreground, rather than daemonizing")

    parser.add_option("-g", "--group", dest="group", action="callback",
                      help="specify group to run as", type="str",
                      callback=getgrname, default=os.getgid())

    parser.add_option("-u", "--user", dest="user", action="callback",
                      help="specify username to run as", type="string",
                      callback=getpwname, default=os.getuid())

    parser.add_option("-l", "--logfile", dest="logfile",
                      default=os.path.join(spydaap.spydaap_dir, "spydaap.log"),
                      help="use .log file (default is ./spydaap.log)")

    parser.add_option("-p", "--pidfile", dest="pidfile",
                      default=os.path.join(spydaap.spydaap_dir, "spydaap.pid"),
                      help="use .pid file (default is ./spydaap.pid)")

    opts, args = parser.parse_args()

    if opts.user == 0 or opts.group == 0:
        sys.stderr.write("spydaap must not run as root\n")
        sys.exit(2)
    #ensure the that the daemon runs a normal user
    os.setegid(opts.group)
    os.seteuid(opts.user)

    if not(opts.daemonize):
        really_main()
    else:
        #redirect outputs to a logfile
        sys.stdout = sys.stderr = Log(open(opts.logfile, 'a+'))
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")   #don't prevent unmounting....
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent, print eventual PID before
                #print "Daemon PID %d" % pid
                open(opts.pidfile,'w').write("%d"%pid)
                sys.exit(0)
        except OSError, e:
            print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
            sys.exit(1)
        really_main()

if __name__ == "__main__":
    main()
