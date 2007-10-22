import hashlib, os, sys

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

dir = "cache"
cache = Cache(dir)
