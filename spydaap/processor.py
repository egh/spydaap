import os, sys, types, struct, md5, StringIO
from daap import do
from spydaap import playlists
from spydaap.mdcache import MetadataCache
import spydaap.parser
import config

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
                        do('dmap.itemid', md.id + 1),
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
                        do('dmap.itemid', md.id + 1),
                        do('dmap.itemname', md.get_name()),
                        do('dmap.containeritemid', md.id + 1)
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
