from spydaap.metadata import mdcache
from spydaap.daap import do

class Builder:
    def __init__(self):
        pass

    def build_list(self, f):
        def build (md):
            return do('dmap.listingitem', 
                      [ do('dmap.itemkind', 2),
                        do('dmap.containeritemid', 2),
                        do('dmap.itemid', md.id + 1),
                        md.get_dmap_raw()
                        ])
        children = [ build (md) for md in mdcache  ]
        file_count = len(children)
        d = do('daap.databasesongs',
               [ do('dmap.status', 200),
                 do('dmap.updatetype', 0),
                 do('dmap.specifiedtotalcount', file_count),
                 do('dmap.returnedcount', file_count),
                 do('dmap.listing',
                    children) ])
        
        f.write(d.encode())

builder = Builder()

