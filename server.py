import web
import daap, sys, os
from daap import do
from processor import Processor
import struct

server_name = "test"
itunes_re = '(?://[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}:[0-9]+)?'

urls = (
    itunes_re + '/', 'server_info',
    itunes_re + '/server-info', 'server_info',
    '/content-codes', 'content_codes',
    '/databases', 'database_list',
    '/databases/([0-9]+)/items', 'item_list',
    '/databases/([0-9]+)/items/([0-9]+).mp3', 'item',
    '/databases/([0-9]+)/containers', 'container_list',
    '/login', 'login',
    '/logout', 'logout',
    '/update', 'update',
    )

class daap_handler:
    def h(self,web,data):
        web.header('Content-Type', 'application/x-dmap-tagged')
        web.header('DAAP-Server', 'Simple')
        web.header('Expires', '-1')
        web.header('Cache-Control', 'no-cache')
        web.header('Accept-Ranges', 'bytes')
        web.header('Content-Language', 'en_us')
        if (type(data) == file):
            web.header("Content-Length", str(os.stat(data.name).st_size))
            return data
        else:
            web.header("Content-Length", str(len(data)))
            print data

class login(daap_handler):
    def GET(self):
        mlog = do('dmap.loginresponse',
                  [ do('dmap.status', 200),
                    do('dmap.sessionid', 101) ])
        return self.h(web,mlog.encode())

class logout:
    def GET(self):
        web.ctx.status = '204 No Content'

class server_info(daap_handler):
    def GET(self):
        msrv = do('dmap.serverinforesponse',
                  [ do('dmap.status', 200),
                    do('dmap.protocolversion', '2.0'),
                    do('daap.protocolversion', '3.0'),
                    do('dmap.itemname', server_name),
                    do('dmap.loginrequired', False),
                    do('dmap.timeoutinterval', 1800),
                    do('dmap.supportsautologout', True),
                    do('dmap.supportsupdate', False),
                    do('dmap.supportspersistentids', True),
                    do('dmap.supportsextensions', True),
                    do('dmap.supportsbrowse', True),
                    do('dmap.supportsquery', True),
                    do('dmap.supportsindex', True),
                    do('dmap.supportsresolve', True),
                    do('dmap.databasescount', 1),
                   ])
        return self.h(web,msrv.encode())

class content_codes(daap_handler):
    def GET(self):
        children = [ do('dmap.status', 200) ]
        for code in daap.dmapCodeTypes.keys():
            (name, dtype) = daap.dmapCodeTypes[code]
            d = do('dmap.dictionary',
                   [ do('dmap.contentcodesnumber', code),
                     do('dmap.contentcodesname', name),
                     do('dmap.contentcodestype',
                        daap.dmapReverseDataTypes[dtype])
                     ])
            children.append(d)
        mccr = do('dmap.contentcodesresponse',
                  children)
        self.h(web, mccr.encode())

class database_list(daap_handler):
    def GET(self):
        d = do('daap.serverdatabases',
               [ do('dmap.status', 200),
                 do('dmap.updatetype', 0),
                 do('dmap.specifiedtotalcount', 1),
                 do('dmap.returnedcount', 1),
                 do('dmap.listing',
                    [ do('dmap.listingitem',
                         [ do('dmap.itemid', 1),
                           do('dmap.persistentid', 1),
                           do('dmap.itemname', server_name),
                           do('dmap.itemcount', 12),
                           do('dmap.containercount', 1)])
                    ])
                ])
        self.h(web,d.encode())

class item_list(daap_handler):
    def GET(self,database_id):
        return self.h(web, open(os.path.join('cache', 'item_list')))

server_revision = 1

class update(daap_handler):
    def GET(self):
        mupd = do('dmap.updateresponse',
                  [ do('dmap.serverrevision', server_revision),
                    do('dmap.status', 200)])
        return self.h(web, mupd.encode())

class item(daap_handler):
    def GET(self,database,item):
        fi = open(os.path.join('cache', 'cache_files'), 'r')
        fi.seek(int(item) * 32)
        cfn = fi.read(32)
        fi.close()
        cfi = open(os.path.join('cache', 'items', cfn))
        fn_len = struct.unpack('!i', cfi.read(4))[0]
        fn = cfi.read(fn_len)
        cfi.close()
        sys.stderr.write(fn)
        return self.h(web, open (fn))

class container_list(daap_handler):
    def GET(self,database):
        d = do('daap.databaseplaylists',
               [ do('dmap.status', 200),
                 do('dmap.updatetype', 0),
                 do('dmap.specifiedtotalcount', 1),
                 do('dmap.returnedcount', 1),
                 do('dmap.listing',
                    [ do('dmap.listingitem',
                         [ do('dmap.itemid', 1),
                           do('dmap.itemcount', 1),
                           do('daap.baseplaylist', 1),
                           do('dmap.itemname', 'Library')
                           ])
                      ])
                 ])
        self.h(web, d.encode())

p = Processor(music_path="/home/egh/music")
p.refresh()
p.build_list()

if __name__ == "__main__": web.run(urls, globals())
