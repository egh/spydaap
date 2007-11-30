import os, struct, hashlib, spydaap.parser, types, spydaap
import config

class MetadataCache:
    parsers = []
    for ms in dir(spydaap.parser):
        m = spydaap.parser.__dict__[ms]
        if type(m) == types.ModuleType:
            for cs in dir(m):
                c = m.__dict__[cs]
                if type(c) == types.ClassType:
                    parsers.append(c())

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
        if (not(os.path.exists(self.dir))):
            os.mkdir(self.dir)
        
    def __iter__(self):
        return MetadataCache.Iter(self.dir)

    def get_item(self, id):
        return MetadataCacheItem(self.dir, id, None)

    def get_item_by_id(self, id):
        fi = open(os.path.join(self.dir, '..', 'index'), 'r')
        fi.seek((int(id) - 1) * 32)
        cfn = fi.read(32)
        fi.close()
        return self.get_item(cfn)

    def build(self, dir):
        for path, dirs, files in os.walk(dir):
            for d in dirs:
                if os.path.islink(os.path.join(path, d)):
                    self.build(os.path.join(path,d))
            files.sort()
            for fn in files:
                ffn = os.path.join(path, fn)
                digest = hashlib.md5(ffn)
                md = self.get_item(digest.hexdigest())
                if (not(md.get_exists()) or \
                        (md.get_mtime() < os.stat(ffn).st_mtime)):
                    for p in self.parsers:
                        if p.understands(ffn):                  
                            (m, name) = p.parse(ffn)
                            if m != None:
                                MetadataCacheItem.write_entry(self.dir, name, ffn, m)
        
        fi = open(os.path.join(self.dir, '..', 'index'), 'w')
        for md in mdcache:
            fi.write(md.pid)
        fi.close()

class MetadataCacheItem:
    @classmethod
    def write_entry(self, dir, name, fn, daap):
        data = "".join([ d.encode() for d in daap])
        data = struct.pack('!i%ss' % len(name), len(name), name) + data
        data = struct.pack('!i%ss' % len(fn), len(fn), fn) + data
        cachefn = os.path.join(dir, hashlib.md5(fn).hexdigest())
        f = open(cachefn, 'w')
        f.write(data)
        f.close()

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

mdcache = MetadataCache(os.path.join(spydaap.cache_dir, "media"))
