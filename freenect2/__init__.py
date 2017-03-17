from contextlib import contextmanager

from ._freenect2 import lib, ffi

_FREENECT2_SINGLETON = None

def _get_freenect2():
    global _FREENECT2_SINGLETON
    if _FREENECT2_SINGLETON is None:
        _FREENECT2_SINGLETON = ffi.gc(
            lib.freenect2_create(), lib.freenect2_dispose)
        lib.freenect2_enumerate_devices(_FREENECT2_SINGLETON)
    return _FREENECT2_SINGLETON

class NoDeviceError(RuntimeError):
    pass

@ffi.def_extern()
def frame_listener_callback(type_, frame_ref, user_data):
    callable_ = ffi.from_handle(user_data)
    assert callable(callable_)
    rv = callable_(type_, frame_ref)
    return rv if rv is not None else 0

def _callable_to_frame_listener(callable_):
    assert callable(callable_)
    handle = ffi.new_handle(callable_)
    return handle, ffi.gc(
        lib.freenect2_frame_listener_create(lib.frame_listener_callback, handle),
        lib.freenect2_frame_listener_dispose
    )

class Device(object):
    def __init__(self, c_object=None):
        if c_object is None:
            c_object = lib.freenect2_open_default_device(_get_freenect2())
        self._c_object = c_object

        if self._c_object == ffi.NULL:
            raise NoDeviceError()

        self._color_frame_listener = None

    def start(self):
        lib.freenect2_device_start(self._c_object)

    def stop(self):
        lib.freenect2_device_stop(self._c_object)

    def close(self):
        lib.freenect2_device_close(self._c_object)

    @property
    def color_frame_listener(self):
        return self._color_frame_listener[0]

    @color_frame_listener.setter
    def color_frame_listener(self, value):
        handle, fl = _callable_to_frame_listener(value)
        lib.freenect2_device_set_color_frame_listener(self._c_object, fl)
        self._color_frame_listener = value, handle, fl

    @contextmanager
    def running(self):
        self.start()
        yield self
        self.stop()
