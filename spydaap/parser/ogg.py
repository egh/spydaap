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

import mutagen, re, spydaap, re, os, sys
from spydaap.daap import do

class OggParser(spydaap.parser.Parser):
    ogg_string_map = {
        'title': 'dmap.itemname',
        'artist': 'daap.songartist',
        'composer': 'daap.songcomposer',
        'genre': 'daap.songgenre',
        'album': 'daap.songalbum'
        }

    ogg_int_map = {
        'bpm': 'daap.songbeatsperminute',
        'date': 'daap.songyear',
        'year': 'daap.songyear',
        'tracknumber': 'daap.songtracknumber',
        'tracktotal': 'daap.songtrackcount',
        'discnumber': 'daap.songdiscnumber'
        }
        
    def handle_string_tags(self, ogg, d):
        for k in ogg.tags.keys():
            if self.ogg_string_map.has_key(k):
                try:
                    tag = [ str(t) for t in ogg.tags[k]]
                    tag = [ t for t in tag if t != ""]
                    d.append(do(self.ogg_string_map[k], "/".join(tag)))
                except: pass
    
    def handle_int_tags(self, ogg, d):
        for k in ogg.tags.keys():
            if self.ogg_int_map.has_key(k):
                try:
                    d.append(do(self.ogg_int_map[k], int(str(ogg.tags[k]))))
                except: pass

    file_re = re.compile(".*\\.[oO][gG]{2}$")
    def understands(self, filename):
        return self.file_re.match(filename)

    def parse(self, filename):
        try:
            ogg = mutagen.File(filename)
            d = []
            if ogg.tags != None:
                if ogg.tags.has_key('TITLE'):
                    name = str(ogg.tags['TITLE'])
                else: name = filename
                
                self.handle_string_tags(ogg, d)
                self.handle_int_tags(ogg, d)
#                self.handle_rating(ogg, d)
            else: 
                name = filename
            statinfo = os.stat(filename)
            d.extend([do('daap.songsize', os.path.getsize(filename)),
                      do('daap.songdateadded', statinfo.st_ctime),
                      do('daap.songdatemodified', statinfo.st_ctime),
                      do('daap.songtime', ogg.info.length * 1000),
                      do('daap.songbitrate', ogg.info.bitrate / 1000),
                      do('daap.songsamplerate', ogg.info.sample_rate),
                      do('daap.songformat', 'ogg'),
                      do('daap.songdescription', 'OGG/Vorbis Audio File'),
                      ])
            return (d, name)
        except Exception, e:
            sys.stderr.write("Caught exception: while processing %s: %s " % (filename, str(e)) )
            return (None, None)    


