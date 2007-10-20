import os, sys, types, struct, md5, StringIO
from daap import do
from spydaap import playlists
import spydaap.parser
import config

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

    def write_entry(self, name, fn, daap):
        data = "".join([ d.encode() for d in daap])
        data = struct.pack('!i%ss' % len(name), len(name), name) + data
        data = struct.pack('!i%ss' % len(fn), len(fn), fn) + data
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

    def get_md(self):
        s = StringIO.StringIO(self.get_dmap_raw())
        l = len(self.get_dmap_raw())
        data = []
        while s.tell() != l:
            d = do()
            d.processData(s)
            data.append(d)
        md = {}
        for d in data:
            md[d.codeName()] = d.value
        return md

class Processor:
    def __init__(self, **kwargs):
        self.music_path = kwargs['music_path']
        if kwargs.has_key('cache_dir'):
            self.cache_dir = kwargs['cache_dir']
        else: self.cache_dir = 'cache'
        self.metadata_cache = MetadataCache(os.path.join(self.cache_dir, 
                                                         'items'))
    parsers = []
    for ms in dir(spydaap.parser):
        m = spydaap.parser.__dict__[ms]
        if type(m) == types.ModuleType:
            for cs in dir(m):
                c = m.__dict__[cs]
                if type(c) == types.ClassType:
                    parsers.append(c())

    def refresh(self, dir=None):
        if dir == None: dir = self.music_path
        for path, dirs, files in os.walk(dir):
            for d in dirs:
                if os.path.islink(os.path.join(path, d)):
                    self.refresh(os.path.join(path,d))
            files.sort()
            for fn in files:
                ffn = os.path.join(path, fn)
                digest = md5.md5(ffn)
                md = self.metadata_cache.get_item(digest.hexdigest())
                if (not(md.get_exists()) or \
                        (md.get_mtime() < os.stat(ffn).st_mtime)):
                    for p in self.parsers:
                        if p.understands(ffn):                  
                            (m, name) = p.parse(ffn)
                            if m != None:
                                self.metadata_cache.write_entry(name, ffn, m)

    def build_list(self):
        def f (md):
            return do('dmap.listingitem', 
                      [ do('dmap.itemkind', 2),
                        do('dmap.containeritemid', 2),
                        do('dmap.itemid', md.id),
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
                        do('dmap.containeritemid', md.id)
                        ])

        for x in dir(playlists):
            pclass = playlists.__dict__[x]
            if type(pclass) == types.ClassType and issubclass(pclass, playlists.Playlist) and pclass.name != None:
                playlist = pclass()
                entries = [n for n in self.metadata_cache if playlist.contains(n)]
                d = do('daap.playlistsongs',
                       [ do('dmap.status', 200),
                         do('dmap.updatetype', 0),
                         do('dmap.specifiedtotalcount', len(entries)),
                         do('dmap.returnedcount', len(entries)),
                         do('dmap.listing',
                            [ build_do (n) for n in entries ])
                         ])
                f = open(os.path.join('cache', 'containers', pclass.name), 'w')
                f.write(d.encode())
                f.close()
