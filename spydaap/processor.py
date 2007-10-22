import os, sys, types, struct, md5, StringIO
from daap import do
from spydaap import playlists
from spydaap.mdcache import mdcache
import spydaap.parser
import config

class Processor:
    def __init__(self):
        pass

    def build_list(self):
        def f (md):
            return do('dmap.listingitem', 
                      [ do('dmap.itemkind', 2),
                        do('dmap.containeritemid', 2),
                        do('dmap.itemid', md.id + 1),
                        md.get_dmap_raw()
                        ])
        children = [ f(md) for md in mdcache  ]
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
        for md in mdcache:
            fi.write(md.pid)
        fi.close()

