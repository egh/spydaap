import os, time

class Playlist:
    name = None
    def sort(self, entries):
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
    
    def sort(self, entries):
        def s(a,b):
            r = cmp(a['daap.songyear'], b['daap.songyear']) 
            if r != 0:
                return r
            else:
                if a.has_key('daap.songartist') and b.has_key('daap.songartist'):
                    return cmp(a['daap.songartist'], b['daap.songartist'])
                elif a.has_key('daap.songartist'):
                    return 1
                elif b.has_key('daap.songartist'):
                    return -1
                else: return 0
        entries.sort(cmp=s)
    
class Recent(Playlist):
     def __init__(self, name, seconds=604800):
     	 self.name = name
	 self.seconds = seconds

     def contains(self, md):
         f_mtime = os.stat(md.get_original_filename()).st_mtime
         return ((f_mtime + self.seconds) > time.time())

class Rating(Playlist):
    def __init__(self, name, rating):
        self.name = name
        self.rating = rating

    def contains(self, md):
        if md.has_key('daap.songuserrating'):
            return md['daap.songuserrating'] >= self.rating
        else: return False
