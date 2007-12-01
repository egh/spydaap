import spydaap, os, struct, md5
from spydaap.daap import do
import config

class ContainerCache(spydaap.cache.OrderedCache):
    def get_item_by_pid(self, pid, n=None):
        return ContainerCacheItem(self, pid, None)

    def build(self):
        def build_do(md):
            d = do('dmap.listingitem',
                   [ do('dmap.itemkind', 2),
                     do('dmap.itemid', md.id),
                     do('dmap.itemname', md.get_name()),
                     do('dmap.containeritemid', md.id)
                     ] )
            return d
        pid_list = []
        for pl in spydaap.container_list:
            entries = [n for n in spydaap.metadata.mdcache if pl.contains(n)]
            pl.sort(entries)
            d = do('daap.playlistsongs',
                   [ do('dmap.status', 200),
                     do('dmap.updatetype', 0),
                     do('dmap.specifiedtotalcount', len(entries)),
                     do('dmap.returnedcount', len(entries)),
                     do('dmap.listing',
                        [ build_do (n) for n in entries ])
                     ])
            ContainerCacheItem.write_entry(self.dir, pl.name, d)
            pid_list.append(md5.md5(pl.name).hexdigest())
        self.build_index(pid_list)
        
class ContainerCacheItem(spydaap.cache.OrderedCacheItem):
    @classmethod
    def write_entry(self, dir, name, d):
        data = struct.pack('!i%ss' % len(name), len(name), name)
        data = data + d.encode()
        cachefn = os.path.join(dir, md5.md5(name).hexdigest())
        f = open(cachefn, 'w')
        f.write(data)
        f.close()

    def __init__(self, cache, pid, id):
        super(ContainerCacheItem, self).__init__(cache, pid, id)
        self.daap_raw = None
        self.name = None

    def read(self):
        f = open(self.path)
        name_len = struct.unpack('!i', f.read(4))[0]
        self.name = f.read(name_len)
        self.daap_raw = f.read()
        f.close()

    def get_daap_raw(self):
        if self.daap_raw == None:
            self.read()
        return self.daap_raw

    def get_name(self):
        if self.name == None:
            self.read()
        return self.name

container_cache = ContainerCache(os.path.join(spydaap.cache_dir, "containers"))

