import hashlib, os, sys, spydaap

class Cache:
    def __init__(self, dir):
        self.dir = dir
        if (not(os.path.exists(self.dir))):
            os.mkdir(self.dir)
    
    def get(self, id, func):
        id = hashlib.md5(id).hexdigest()
        fn = os.path.join(self.dir, id)
        if (not(os.path.exists(fn))):
            f = open(fn, 'w')
            func (f)
            f.close()
        sys.stderr.write(str(fn))
        return open(fn)

class OrderedCache(object):
    class Iter:
        def __init__(self, cache):
            self.cache = cache
            self.files = [ f for f in os.listdir(self.cache.dir) if f != "index"]
            self.files.sort()
            self.n = 0

        def __iter__(self):
            return self
        
        def next(self):
            if self.n == len(self.files):
                raise StopIteration
            fn = self.files[self.n]
            self.n = self.n + 1 
            return self.cache.get_item_by_pid(fn, (self.n - 1))

    def __init__(self, dir):
        self.dir = dir
        if (not(os.path.exists(self.dir))):
            os.mkdir(self.dir)
        
    def __iter__(self):
        return OrderedCache.Iter(self)

    def get_item_by_id(self, id):
        fi = open(os.path.join(self.dir, 'index'), 'r')
        fi.seek((int(id) - 1) * 32)
        cfn = fi.read(32)
        fi.close()
        return self.get_item_by_pid(cfn, id)

    def build_index(self):
        fi = open(os.path.join(self.dir, 'index'), 'w')
        for i in self:
            fi.write(i.pid)
        fi.close()

class OrderedCacheItem(object):
    def __init__(self, cache, pid, id):
        self.cache = cache
        self.pid = pid
        self.id = id
        self.path = os.path.join(self.cache.dir, pid)

    def get_mtime(self):
        return os.stat(self.path).st_mtime

    def get_exists(self):
        return os.path.exists(self.path)
 
    def get_id(self):
        return self.id
    
    def get_pid(self):
        return self.pid    

cache = Cache(spydaap.cache_dir)
