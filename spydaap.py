import web, sys, os, struct, re, select, spydaap.daap, pybonjour
from spydaap.daap import do
from spydaap.processor import Processor
import spydaap.cache
import config

#itunes sends request for:
#GET daap://192.168.1.4:3689/databases/1/items/626.mp3?seesion-id=1
#so we must hack the urls; annoying.

itunes_re = '(?://[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}:[0-9]+)?'
drop_q = '(?:\\?.*)?'
urls = (
    itunes_re + '/', 
    'server_info', #
    itunes_re + '/server-info', 
    'server_info', #
    '/content-codes', 
    'content_codes', #
    '/databases', 
    'database_list', #
    '/databases/([0-9]+)/items', 
    'item_list', #
    itunes_re + '/databases/([0-9]+)/items/([0-9]+)\\.([0-9a-z]+)' + drop_q, 
    'item', #
    '/databases/([0-9]+)/containers', 
    'container_list', #
    itunes_re + '/databases/([0-9]+)/containers/([0-9]+)/items', 
    'container_item_list', #
    '/login', 
    'login', #
    '/logout', 
    'logout', #
    '/update',
    'update', #
    )

class daap_handler:
    def h(self,web,data):
        web.header('Content-Type', 'application/x-dmap-tagged')
        web.header('DAAP-Server', 'Simple')
        web.header('Expires', '-1')
        web.header('Cache-Control', 'no-cache')
        web.header('Accept-Ranges', 'bytes')
        web.header('Content-Language', 'en_us')
        if (hasattr(data, 'next')):
            try:
                web.header("Content-Length", str(os.stat(data.name).st_size))
            except: pass
            return data
        else:
            try:
                web.header("Content-Length", str(len(data)))
            except: pass
            sys.stdout.write(data)

session_id = 1
class login(daap_handler):
    def GET(self):
        mlog = do('dmap.loginresponse',
                  [ do('dmap.status', 200),
                    do('dmap.sessionid', session_id) ])
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
                    do('dmap.timeoutinterval', 1800),
                    do('dmap.itemname', spydaap.server_name),
                    do('dmap.loginrequired', 0),
                    do('dmap.authenticationmethod', 0),
                    do('dmap.supportsextensions', 0),
                    do('dmap.supportsindex', 0),
                    do('dmap.supportsbrowse', 0),
                    do('dmap.supportsquery', 0),
                    do('dmap.supportspersistentids', 0),
                    do('dmap.databasescount', 1),                
                    #do('dmap.supportsautologout', 0),
                    #do('dmap.supportsupdate', 0),
                    #do('dmap.supportsresolve', 0),
                   ])
        return self.h(web,msrv.encode())

class content_codes(daap_handler):
    def GET(self):
        children = [ do('dmap.status', 200) ]
        for code in spydaap.daap.dmapCodeTypes.keys():
            (name, dtype) = spydaap.daap.dmapCodeTypes[code]
            d = do('dmap.dictionary',
                   [ do('dmap.contentcodesnumber', code),
                     do('dmap.contentcodesname', name),
                     do('dmap.contentcodestype',
                        spydaap.daap.dmapReverseDataTypes[dtype])
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
                           do('dmap.itemname', spydaap.server_name),
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
                  [ do('dmap.status', 200),
                    do('dmap.serverrevision', server_revision),
                    ])
        return self.h(web, mupd.encode())

class ContentRangeFile:
    def __init__(self, parent, start, end=None, chunk=1024):
        self.parent = parent
        self.start = start
        self.end = end
        self.chunk = chunk
        self.parent.seek(self.start)
        self.read = start

    def next(self):
        to_read = self.chunk
        if (self.end != None):
            if (self.read >= self.end):
                sys.stderr.write('done')
                self.parent.close()
                raise StopIteration
            if (to_read + self.read > self.end):
                to_read = self.end - self.read
            retval = self.parent.read(to_read)
            self.read = self.read + len(retval)
        else: retval = self.parent.read(to_read)
        if retval == '':
            self.parent.close()
            raise StopIteration
        else: return retval

    def __iter__(self):
        return self

class item(daap_handler):
    def GET(self,database,item,format):
        #web.request.chunked_write = True
        sys.stderr.write(str(web.ctx.environ))
        fi = open(os.path.join('cache', 'cache_files'), 'r')
        fi.seek((int(item) - 1) * 32)
        cfn = fi.read(32)
        fi.close()
        cfi = open(os.path.join('cache', 'items', cfn))
        fn_len = struct.unpack('!i', cfi.read(4))[0]
        fn = cfi.read(fn_len)
        cfi.close()
        if (web.ctx.environ.has_key('HTTP_RANGE')):
            rs = web.ctx.environ['HTTP_RANGE']
            m = re.compile('bytes=([0-9]+)-([0-9]+)?').match(rs)
            (start, end) = m.groups()
            if end != None: end = int(end)
            else: end = os.stat(fn).st_size
            start = int(start)
            f = ContentRangeFile(open(fn), start, end)
            web.ctx.status = "206 Partial Content"
            web.header("Content-Range", 
                       "bytes " + str(start) + "-"
                       + str(end) + "/"
                       + str(os.stat(fn).st_size))
        else: f = open(fn)
        return self.h(web, f)

class container_list(daap_handler):
    def GET(self,database):
        container_files = os.listdir('cache/containers')
        container_files.sort()
        container_do = []
        for i, fn in enumerate(container_files):
            container_do.append(do('dmap.listingitem',
                                   [ do('dmap.itemid', i + 1 ),
                                     do('dmap.containeritemid', i + 1),
                                     do('dmap.itemname', fn) ]))
        d = do('daap.databaseplaylists',
               [ do('dmap.status', 200),
                 do('dmap.updatetype', 0),
                 do('dmap.specifiedtotalcount', len(container_do)),
                 do('dmap.returnedcount', len(container_do)),
                 do('dmap.listing',
                    container_do)
                 ])
        self.h(web, d.encode())

class container_item_list(daap_handler):
    def GET(self, did, cid):
        container_files = os.listdir('cache/containers/')
        container_files.sort()
        return self.h(web, open(os.path.join('cache', 'containers', 
                                             container_files[int(cid) - 1])))

media_path = "media"
p = Processor()
spydaap.mdcache.mdcache.build("media/")
p.build_list()
p.build_playlists()

def register_callback(sdRef, flags, errorCode, name, regtype, domain):
    if errorCode == pybonjour.kDNSServiceErr_NoError:
        print 'Registered service:'
        print '  name    =', name
        print '  regtype =', regtype
        print '  domain  =', domain

sdRef = pybonjour.DNSServiceRegister(name = spydaap.server_name,
                                     regtype = "_daap._tcp",
                                     port = spydaap.port,
                                     callBack = register_callback)

while True:
    ready = select.select([sdRef], [], [])
    if sdRef in ready[0]:
        pybonjour.DNSServiceProcessResult(sdRef)
        break

#hacky; there is a better way
sys.argv.append(str(spydaap.port))

web.webapi.internalerror = web.debugerror
#if __name__ == "__main__": web.run(urls, globals())
web.wsgi.runwsgi(web.webapi.wsgifunc(web.webpyfunc(urls, globals())))
sdRef.close()
