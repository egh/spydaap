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
