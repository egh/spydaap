from mutagen.id3 import ID3NoHeaderError, ID3UnsupportedVersionError, ID3
import os, sys, types, struct, md5
from mutagen.mp3 import MP3
from daap import do
import playlists
ID3.PEDANTIC = False

class MetadataCache:
    class Iter:
        def __init__(self, dir):
            self.dir = dir
            self.files = os.listdir(self.dir)
            self.files.sort()
            self.n = 0
        
        def __iter__(self):
            return self
        
        def next(self):
            if self.n == len(self.files):
                raise StopIteration
            fn = self.files[self.n]
            self.n = self.n + 1 
            return MetadataCacheItem(self.dir, fn, (self.n - 1))

    def __init__(self, dir):
        self.dir = dir
        
    def __iter__(self):
        return MetadataCache.Iter(self.dir)

    def get_item(self, id):
        return MetadataCacheItem(self.dir, id, None)

    def write_entry(self, fn, name, daap):
        data = "".join([ d.encode() for d in daap])
        data = struct.pack('!i%ss' % len(fn), len(fn), fn) + data
        data = struct.pack('!i%ss' % len(name), len(name), name) + data
        cachefn = os.path.join(self.dir, md5.md5(fn).hexdigest())
        f = open(cachefn, 'w')
        f.write(data)
        f.close()

class MetadataCacheItem:
    def __init__(self, dir, pid, id):
        self.dir = dir
        self.pid = pid
        self.id = id
        self.fn = os.path.join(dir, pid)
        self.file = None
        self.daap = None
        self.name = None
        self.original_filename = None
        self.daap_raw = None

    def get_mtime(self):
        return os.stat(self.fn).st_mtime

    def get_exists(self):
        return os.path.exists(self.fn)
 
    def get_id(self):
        return self.id
    
    def get_pid(self):
        return self.pid
    
    def read(self):
        f = open(self.fn)
        fn_len = struct.unpack('!i', f.read(4))[0]
        self.original_filename = f.read(fn_len)
        name_len = struct.unpack('!i', f.read(4))[0]
        self.name = f.read(name_len)
        self.daap_raw = f.read()
        f.close()

    def get_original_filename(self):
        if self.original_filename == None:
            self.read()
        return self.original_filename 
    
    def get_name(self):
        if self.name == None:
            self.read()
        return self.name

    def get_dmap_raw(self):
        if self.daap_raw == None:
            self.read()
        return self.daap_raw

class Processor:
    def __init__(self, **kwargs):
        self.music_path = kwargs['music_path']
        if kwargs.has_key('cache_dir'):
            self.cache_dir = kwargs['cache_dir']
        else: self.cache_dir = 'cache'
        self.metadata_cache = MetadataCache(os.path.join(self.cache_dir, 'items'))

    mp3_string_map = {
        'TIT1': 'daap.songgrouping',
        'TIT2': 'dmap.itemname',
        'TPE1': 'daap.songartist',
        'TCOM': 'daap.songcomposer',
        'TCON': 'daap.songgenre',
        'TPE1': 'daap.songartist',
        'TALB': 'daap.songalbum',
        }

    mp3_int_map = {
        'TDOR': 'daap.songyear',
        'TBPM': 'daap.songbeatsperminute',
        #'TLEN': 'daap.songtime',
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
        try:
            mp3 = MP3(filename)
            if mp3.tags != None:
                d = [ do(self.mp3_string_map[k], str(mp3.tags[k])) for k in mp3.tags.keys() if self.mp3_string_map.has_key(k) ]
                self.add_int_tags(mp3, d)
                statinfo = os.stat(filename)
                d.extend([do('daap.songsize', os.path.getsize(filename)),
                          do('daap.songdateadded', statinfo.st_ctime),
                          do('daap.songdatemodified', statinfo.st_mtime),
                          do('daap.songtime', mp3.info.length * 1000),
                          do('daap.songbitrate', mp3.info.bitrate),
                          do('daap.songsamplerate', mp3.info.sample_rate)
                          ])
                try:
                    if mp3.tags.has_key('TRCK'):
                        t = str(mp3.tags['TRCK']).split('/')
                        d.append(do('daap.songtracknumber', int(t[0])))
                        if (len(t) == 2):
                            d.append(do('daap.songtrackcount', int(t[1])))                     
                except:
                    pass
                if mp3.tags.has_key('TIT2'):
                    name = str(mp3.tags['TIT2'])
                else: name = filename
                return (d, name)
            else:
                return (None, None)
        except Exception, e:
            sys.stderr.write("Caught exception: while processing %s: %s " % (filename, str(e)) )
            return (None, None)
            
    def refresh(self):
        for path, dirs, files in os.walk(self.music_path):
            files.sort()
            for fn in files:
                if not fn.lower().endswith('.mp3'): continue
                ffn = os.path.join(path, fn)
                digest = md5.md5(ffn)
                md = self.metadata_cache.get_item(digest.hexdigest())
                if (not(md.get_exists()) or (md.get_mtime() < os.stat(ffn).st_mtime)):
                    (m, name) = self.mp3(ffn)
                    if m != None:
                        self.metadata_cache.write_entry(name, ffn, m)

    def build_list(self):
        def f (md):
            return do('dmap.listingitem', 
                      [ do('dmap.itemkind', 2),
                        do('dmap.containeritemid', 2),
                        do('dmap.itemid', md.id),
                        do('daap.songformat', 'mp3'),
                        do('daap.songdescription', 'MPEG Audio File'),
                        md.get_dmap_raw()
                        ])
        children = [ f(md) for md in self.metadata_cache  ]
        file_count = len(children)
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
        for md in self.metadata_cache:
            fi.write(md.pid)
        fi.close()

    def build_playlists(self):
        def build_do(md):
            return do('dmap.listingitem',
                      [ do('dmap.itemkind', 2),
                        do('dmap.itemid', md.id),
                        do('dmap.itemname', md.get_name()),
                        do('dmap.containeritemid', 111124)
                        ])

        for x in dir(playlists):
            p = eval('playlists.' + x)
            if type(p) == types.ClassType and issubclass(p, playlists.Library):                
                playlist = p()
                entries = [n for n in self.metadata_cache if playlist.contains(n)]
            d = do('daap.playlistsongs',
                   [ do('dmap.status', 200),
                     do('dmap.updatetype', 0),
                     do('dmap.specifiedtotalcount', len(entries)),
                     do('dmap.returnedcount', len(entries)),
                     do('dmap.listing',
                       [ build_do (n) for n in entries ])
                     ])
            f = open(os.path.join('cache', 'playlist_1'), 'w')
            f.write(d.encode())
            f.close()
