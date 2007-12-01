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
        if not(md.has_key('daap.songgenre')): return False
        else:
            songgenre = md['daap.songgenre'].lower()
            if type(self.genre) == str:
                return songgenre == self.genre
            elif type(self.genre) == list:
                return songgenre in self.genre

class YearRange(Playlist):
    def __init__(self, name, first,last=None):
        self.name = name
        if last == None:
            last = first
        self.last = last
        self.first = first

    def contains(self, md):
        if not(md.has_key('daap.songyear')): return False
        else:
            year = md['daap.songyear']
            return year >= self.first and year <= self.last

class Recent(Playlist):
     def __init__(self, name, seconds=604800):
     	 self.name = name
	 self.seconds = seconds

     def contains(self, md):
         f_ctime = os.stat(md.get_original_filename()).st_ctime
         return ((f_ctime + self.seconds) > time.time())

class Rating(Playlist):
    def __init__(self, name, rating):
        self.name = name
        self.rating = rating

    def contains(self, md):
        if md.has_key('daap.songuserrating'):
            return md['daap.songuserrating'] >= self.rating
        else: return False
