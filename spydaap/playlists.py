from spydaap.daap import do

class Builder:
    def build(self, f):
        def build_do(md):
            return do('dmap.listingitem',
                      [ do('dmap.itemkind', 2),
                        do('dmap.itemid', md.id + 1),
                        do('dmap.itemname', md.get_name()),
                        do('dmap.containeritemid', md.id + 1)
                        ] )

        for x in dir(self.__module__):
            pclass = self.__module__.__dict__[x]
            if type(pclass) == types.ClassType and \
                    issubclass(pclass, Playlist) and \
                    pclass.name != None:
                pl = pclass()
                entries = [n for n in self.metadata_cache if pl.contains(n)]
                d = do('daap.playlistsongs',
                       [ do('dmap.status', 200),
                         do('dmap.updatetype', 0),
                         do('dmap.specifiedtotalcount', len(entries)),
                         do('dmap.returnedcount', len(entries)),
                         do('dmap.listing',
                            [ build_do (n) for n in entries ])
                         ])
                f.write(d.encode())

class Playlist:
    name = None
    pass

class Library(Playlist):
    name = "Library"
    def contains(self, md):
        return True

class Genre(Playlist):
    def contains(self, md):
        h = md.get_md()
        if not(h.has_key('daap.songgenre')): return False
        else:
            songgenre = h['daap.songgenre'].lower()
            matchgenre = self.__class__.genre
            if type(matchgenre) == str:
                return songgenre == matchgenre
            elif type(matchgenre) == list:
                return songgenre in matchgenre

#class Reggae(Genre):
#    name = "reggae"
#    genre = ["reggae", "reggae: dub", "dub"]

#class Classical(Genre):
#    name = "classical"
#    genre = ["classical", "avant garde"]
