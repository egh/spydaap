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

class OrderedCache:
    class Iter:
        def __init__(self, cache):
            self.cache = cache
            self.files = os.listdir(self.cache.dir)
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
        fi = open(os.path.join(self.dir, '..', 'index'), 'r')
        fi.seek((int(id) - 1) * 32)
        cfn = fi.read(32)
        fi.close()
        return self.get_item_by_pid(cfn, id)

class OrderedCacheItem:
    pass

cache = Cache(spydaap.cache_dir)
