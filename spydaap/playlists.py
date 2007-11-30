import os, time

class Playlist:
    name = None
    pass

class Library(Playlist):
    def __init__(self):
        self.name = "Library"

    def contains(self, md):
        return True

class Genre(Playlist):
    def __init__(self, name, genre):
        self.name = name
        self.genre = genre
    
    def contains(self, md):
        h = md.get_md()
        if not(h.has_key('daap.songgenre')): return False
        else:
            songgenre = h['daap.songgenre'].lower()
            if type(self.genre) == str:
                return songgenre == self.genre
            elif type(self.genre) == list:
                return songgenre in self.genre

class Recent(Playlist):
     def __init__(self, name, seconds=604800):
     	 self.name = name
	 self.seconds = seconds

     def contains(self, md):
         f_ctime = os.stat(md.get_original_filename()).st_ctime
         return ((f_ctime + self.seconds) > time.time())
