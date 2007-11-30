import spydaap
from spydaap.parser import mp3

#to process .mov files
#from spydaap.parser import mp3,mov

#spydaap.server_name = "spydaap"
#spydaap.port = 3689

#top path to scan for media
#spydaap.media_path = "media"

#spydaap.cache_dir = 'cache'

spydaap.container_list.append(spydaap.playlists.Genre('reggae', ["reggae", "reggae: dub", "dub"]))
spydaap.container_list.append(spydaap.playlists.Recent('last 30 days', (60 * 60 * 24 * 30)))
