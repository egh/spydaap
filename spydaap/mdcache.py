import os, struct

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
