class Playlist:
    pass

class Library(Playlist):
    name = "Library"
    def contains(self, md):
        return True
