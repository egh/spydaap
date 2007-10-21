import re, spydaap, os, sys
from spydaap.daap import do

class MovParser(spydaap.parser.Parser):
    file_re = re.compile(".*\\.[mV][oO][vV]$")
    def understands(self, filename):
        return self.file_re.match(filename)
    
    def parse(self, filename):
        name = filename
        statinfo = os.stat(filename)
        d = [ do ('daap.songsize', os.path.getsize(filename)),
              do ('daap.songdateadded', statinfo.st_mtime),
              do ('daap.songdatemodified', statinfo.st_mtime),
              do ('dmap.itemname', name),
              do ('daap.songalbum', ''),
              do ('daap.songartist', ''),
              do ('daap.songbitrate', 0),
              do ('daap.songcomment', ''),
              do ('daap.songdescription', 'QuickTime movie file'),
              do ('daap.songformat', 'mov'),
              do ('com.apple.itunes.mediakind', 2),
              do ('com.apple.itunes.has-video', True)
              ]
        return (d, name)
    
