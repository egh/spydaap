# adopted from http://stackp.online.fr/?p=35

__all__ = ["ZeroconfImpl"]

import socket
import logging

logger = logging.getLogger(__name__)


class ZeroconfImpl(object):
    """A simple class to publish a network service with zeroconf using
    avahi or python-zeroconf
    """

    class Helper(object):

        def __init__(self, name, port, **kwargs):
            self.name = name
            self.port = port
            self.stype = kwargs.get('stype', "_http._tcp")
            self.domain = kwargs.get('domain', '')
            self.host = kwargs.get('host', '')
            self.text = kwargs.get('text', '')

    class Zeroconf(Helper):
        
        def publish(self):
            import zeroconf
            
            # zeroconf doesn't do this for us
            # .. pick one at random? Ideally, zeroconf would publish all valid
            #    addresses as the A record.. but doesn't seem to do so
            addrs = zeroconf.get_all_addresses(socket.AF_INET)
            address = None
            if addrs:
                for addr in addrs:
                    if addr != '127.0.0.1':
                        address = socket.inet_aton(addrs[0])
            
            type_ = self.stype + ".local."
            self.info = zeroconf.ServiceInfo(
                type_,
                self.name + "." + type_,
                address=address,
                port=self.port,
                properties=self.text,
                server=self.host if self.host else None
            )
            
            self.zc = zeroconf.Zeroconf()
            self.zc.register_service(self.info)
        
        def unpublish(self):
            self.zc.unregister_service(self.info)
            self.zc.close()

    class Avahi(Helper):

        def publish(self, ipv4=True, ipv6=True):
            import dbus
            import avahi
            bus = dbus.SystemBus()
            server = dbus.Interface(
                bus.get_object(
                    avahi.DBUS_NAME,
                    avahi.DBUS_PATH_SERVER),
                avahi.DBUS_INTERFACE_SERVER)

            self.group = dbus.Interface(
                bus.get_object(avahi.DBUS_NAME,
                               server.EntryGroupNew()),
                avahi.DBUS_INTERFACE_ENTRY_GROUP)

            if ipv4 and ipv6:
                proto = avahi.PROTO_UNSPEC
            elif ipv6:
                proto = avahi.PROTO_INET6
            else:  # we don't let them both be false
                proto = avahi.PROTO_INET

            self.group.AddService(avahi.IF_UNSPEC, proto,
                                  dbus.UInt32(0), self.name, self.stype, self.domain,
                                  self.host, dbus.UInt16(self.port), self.text)
            self.group.Commit()

        def unpublish(self):
            self.group.Reset()

    def __init__(self, *args, **kwargs):
        zeroconf = None
        avahi = None
        
        try:
            import zeroconf
        except ImportError:
            try:
                import avahi
                import dbus
            except ImportError:
                pass
        
        if zeroconf:
            logger.info("zeroconf implementation is zeroconf")
            self.helper = ZeroconfImpl.Zeroconf(*args, **kwargs)
            
        elif avahi:
            logger.info("zeroconf implementation is avahi")
            self.helper = ZeroconfImpl.Avahi(*args, **kwargs)
        
        else:
            logger.warning('zeroconf implementation not found, cannot announce presence')
            self.helper = None


    def publish(self, *args, **kwargs):
        if self.helper is not None:
            self.helper.publish(*args, **kwargs)

    def unpublish(self):
        if self.helper is not None:
            self.helper.unpublish()
