import mutagen.id3, mutagen.mp3, re, spydaap, re, os, sys
from spydaap.daap import do
mutagen.id3.ID3.PEDANTIC = False

class Mp3Parser(spydaap.parser.Parser):
    mp3_string_map = {
        'TIT1': 'daap.songgrouping',
        'TIT2': 'dmap.itemname',
        'TPE1': 'daap.songartist',
        'TCOM': 'daap.songcomposer',
        'TCON': 'daap.songgenre',
        'TPE1': 'daap.songartist',
        'TALB': 'daap.songalbum',
        }

    mp3_int_map = {
        'TBPM': 'daap.songbeatsperminute',
        'TDRC': 'daap.songyear'
        #'TLEN': 'daap.songtime',
        }
#do('daap.songdiscnumber', 1),
#        do('daap.songgenre', 'Test'),
#        do('daap.songdisccount', 1),
#        do('daap.songcompilation', False),
#        do('daap.songuserrating', 1),
                                                     
    def add_int_tags(self, mp3, d):
        for k in mp3.tags.keys():
            if self.mp3_int_map.has_key(k):
                try:
                    d.append(do(self.mp3_int_map[k], int(str(mp3.tags[k]))))
                except: pass

    def handle_rating(self, mp3, d):
        try:
            if mp3.tags.has_key('POPM'):
                rating = int(mp3.tags['POPM'] * (0.39215686274509803))
                d.append(do('daap.songuserrating', rating))
        except: pass

    file_re = re.compile(".*\\.[mM][pP]3$")
    def understands(self, filename):
        return self.file_re.match(filename)

    def parse(self, filename):
        try:
            mp3 = mutagen.mp3.MP3(filename)
            if mp3.tags != None:
                d = [ do(self.mp3_string_map[k], str(mp3.tags[k])) 
                      for k in mp3.tags.keys() 
                      if self.mp3_string_map.has_key(k) ]
                self.add_int_tags(mp3, d)
                self.handle_rating (mp3, d)
                try:
                    if mp3.tags.has_key('TRCK'):
                        t = str(mp3.tags['TRCK']).split('/')
                        d.append(do('daap.songtracknumber', int(t[0])))
                        if (len(t) == 2):
                            d.append(do('daap.songtrackcount', int(t[1])))
                except: pass
                if mp3.tags.has_key('TIT2'):
                    name = str(mp3.tags['TIT2'])
                else: name = filename
            else: 
                d = []
                name = filename
            statinfo = os.stat(filename)
            d.extend([do('daap.songsize', os.path.getsize(filename)),
                      do('daap.songdateadded', statinfo.st_ctime),
                      do('daap.songdatemodified', statinfo.st_ctime),
                      do('daap.songtime', mp3.info.length * 1000),
                      do('daap.songbitrate', mp3.info.bitrate / 1000),
                      do('daap.songsamplerate', mp3.info.sample_rate),
                      do('daap.songformat', 'mp3'),
                      do('daap.songdescription', 'MPEG Audio File'),
                      ])
            return (d, name)
        except Exception, e:
            sys.stderr.write("Caught exception: while processing %s: %s " % (filename, str(e)) )
            return (None, None)
