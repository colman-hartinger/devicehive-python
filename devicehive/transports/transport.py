import uuid
import sys
import threading


class Transport(object):
    """Transport class."""

    REQUEST_ID_KEY = 'requestId'
    REQUEST_ACTION_KEY = 'action'

    def __init__(self, name, exception, data_format_class, data_format_options,
                 handler_class, handler_options):
        self._name = name
        self._exception = exception
        self._data_format = data_format_class(**data_format_options)
        self._data_type = self._data_format.data_type
        self._handler = handler_class(self, **handler_options)
        self._connection_thread = None
        self._connected = False
        self._exception_info = None

    @staticmethod
    def _uuid():
        return str(uuid.uuid1())

    def _encode(self, obj):
        return self._data_format.encode(obj)

    def _decode(self, data):
        return self._data_format.decode(data)

    def _handle_connect(self):
        self._handler.handle_connect()

    def _handle_event(self, event):
        self._handler.handle_event(event)

    def _handle_disconnect(self):
        self._handler.handle_disconnect()

    def _ensure_not_connected(self):
        if not self._connected:
            return
        raise self._exception('Connection has already created.')

    def _ensure_connected(self):
        if self._connected:
            return
        raise self._exception('Connection has not created.')

    def _connection(self, url, options):
        try:
            self._connect(url, **options)
            self._receive()
            self._disconnect()
        except BaseException:
            self._exception_info = sys.exc_info()

    def _connect(self, url, **options):
        raise NotImplementedError

    def _receive(self):
        raise NotImplementedError

    def _disconnect(self):
        raise NotImplementedError

    @property
    def name(self):
        return self._name

    @property
    def connected(self):
        return self._connected

    @property
    def exception_info(self):
        return self._exception_info

    def connect(self, url, **options):
        self._ensure_not_connected()
        self._connection_thread = threading.Thread(target=self._connection,
                                                   args=(url, options))
        self._connection_thread.name = '%s-transport-connection' % self._name
        self._connection_thread.daemon = True
        self._connection_thread.start()

    def disconnect(self):
        self._ensure_connected()
        self._connected = False

    def join(self, timeout=None):
        self._connection_thread.join(timeout)

    def send_request(self, action, request, **params):
        raise NotImplementedError

    def request(self, action, request, **params):
        raise NotImplementedError


class TransportException(IOError):
    """Transport exception."""
