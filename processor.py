from mutagen.id3 import ID3NoHeaderError, ID3UnsupportedVersionError, ID3
import os
from mutagen.mp3 import MP3
from daap import do
import struct
import md5

class Processor:
    def __init__(self, **kwargs):
        self.music_path = kwargs['music_path']
        if kwargs.has_key('cache_dir'):
            self.cache_dir = kwargs['cache_dir']
        else: self.cache_dir = 'cache'
        self.items_cache_dir = os.path.join(self.cache_dir, 'items')

    mp3_string_map = {
        'TIT2': 'dmap.itemname',
        'TPE1': 'daap.songartist',
        'TALB': 'daap.songalbum'
        }

    mp3_int_map = {
        'TDOR': 'daap.songyear',
        'TBPM': 'daap.songbeatsperminute'
        }
#do('daap.songdiscnumber', 1),
#        do('daap.songgenre', 'Test'),
#        do('daap.songdisccount', 1),
#        do('daap.songcompilation', False),
#        do('daap.songuserrating', 1),
                                                     
    def add_int_tags(self, mp3, d):
        for k in mp3.tags.keys():
            if self.mp3_int_map.has_key(k):
                try: d.append(do(mp3_int_map[k], int(str(mp3.tags[k]))))
                except: pass
    def mp3(self, filename):
#        try:
            mp3 = MP3(filename)
            if mp3.tags != None:
                d = [ do(self.mp3_string_map[k], str(mp3.tags[k])) for k in mp3.tags.keys() if self.mp3_string_map.has_key(k) ]
                self.add_int_tags(mp3, d)
                statinfo = os.stat(filename)
                print mp3.info.length
                d.extend([do('daap.songsize', os.path.getsize(filename)),
                          #do('daap.songdateadded', statinfo.st_ctime),
                          #do('daap.songdatemodified', statinfo.st_mtime),
                          do('daap.songtime', mp3.info.length),
                          do('daap.songbitrate', mp3.info.bitrate),
                          do('daap.songsamplerate', mp3.info.sample_rate)])
                try:
                    if mp3.tags.has_key('TRCK'):
                        t = str(mp3.tags['TRCK']).split('/')
                        d.append(do('daap.songtracknumber', int(t[0])))
                        if (len(t) == 2):
                            d.append(do('daap.songtrackcount', int(t[1])))                     
                except:
                    pass
                return d
            else:
                return None
 #       except Exception:
  #          return None
            
    def refresh(self):
        from traceback import print_exc
        from mutagen.id3 import ID3NoHeaderError, ID3UnsupportedVersionError
        from mutagen.mp3 import MP3
        ID3.PEDANTIC = False
        for path, dirs, files in os.walk(self.music_path):
            files.sort()
            for fn in files:
                if not fn.lower().endswith('.mp3'): continue
                ffn = os.path.join(path, fn)
                digest = md5.md5(ffn)
                cachefn = os.path.join(self.items_cache_dir, digest.hexdigest())
                if (not(os.path.exists(cachefn)) or (os.stat(cachefn).st_mtime < os.stat(ffn).st_mtime)):
                    m = self.mp3(ffn)
                    if m != None:
                        data = "".join([ d.encode() for d in m])
                        data = struct.pack('!i%ss' % len(ffn), len(ffn), ffn) + data
                        f = open(cachefn, 'w')
                        f.write(data)
                        f.close()

    def build_list(self):
        files = os.listdir(self.items_cache_dir)
        files
        files.sort()
        def f (i, fn):
            fi = open(os.path.join(self.items_cache_dir, fn))
            fn_len = struct.unpack('!i', fi.read(4))[0]
            fi.read(fn_len)
            return do('dmap.listingitem', 
                      [ do('dmap.itemkind', 2),
                        do('dmap.containeritemid', 2),
                        do('dmap.itemid', i),
                        do('daap.songformat', 'mp3'),
                        do('daap.songdescription', 'MPEG Audio File'),
                        fi.read()
                        ])
        children = [ f (i, fn) for i, fn in enumerate(files) ]
        file_count = len(files)
        d = do('daap.databasesongs',
               [ do('dmap.status', 200),
                 do('dmap.updatetype', 0),
                 do('dmap.specifiedtotalcount', file_count),
                 do('dmap.returnedcount', file_count),
                 do('dmap.listing',
                    children) ])
        fi = open(os.path.join(self.cache_dir, 'item_list'), 'w')        
        fi.write(d.encode())
        fi.close()
        fi = open(os.path.join(self.cache_dir, 'cache_files'), 'w')
        for n in files:
            fi.write(n)
        fi.close()
