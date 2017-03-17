from contextlib import contextmanager
import enum

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

class FrameType(enum.Enum):
    Color = lib.FRAME_TYPE_COLOR
    Ir = lib.FRAME_TYPE_IR
    Depth = lib.FRAME_TYPE_DEPTH

class FrameFormat(enum.Enum):
    Invalid = lib.FRAME_FORMAT_INVALID
    Raw = lib.FRAME_FORMAT_RAW
    Float = lib.FRAME_FORMAT_FLOAT
    BGRX = lib.FRAME_FORMAT_BGRX
    RGBX = lib.FRAME_FORMAT_RGBX
    Gray = lib.FRAME_FORMAT_GRAY

@ffi.def_extern()
def frame_listener_callback(type_, frame_ref, user_data):
    callable_ = ffi.from_handle(user_data)
    assert callable(callable_)
    frame = Frame(ffi.gc(frame_ref, lib.freenect2_frame_dispose))
    callable_(FrameType(type_), frame)
    return 1

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

class Frame(object):
    def __init__(self, frame_ref):
        self._c_object = frame_ref

    @property
    def width(self):
        return lib.freenect2_frame_get_width(self._c_object)

    @property
    def height(self):
        return lib.freenect2_frame_get_height(self._c_object)

    @property
    def bytes_per_pixel(self):
        return lib.freenect2_frame_get_bytes_per_pixel(self._c_object)

    @property
    def data(self):
        data_ptr = lib.freenect2_frame_get_data(self._c_object)
        return ffi.buffer(
            data_ptr, self.width * self.height * self.bytes_per_pixel)

    @property
    def timestamp(self):
        return lib.freenect2_frame_get_timestamp(self._c_object)

    @property
    def sequence(self):
        return lib.freenect2_frame_get_sequence(self._c_object)

    @property
    def exposure(self):
        return lib.freenect2_frame_get_exposure(self._c_object)

    @property
    def gain(self):
        return lib.freenect2_frame_get_gain(self._c_object)

    @property
    def gamma(self):
        return lib.freenect2_frame_get_gamma(self._c_object)

    @property
    def status(self):
        return lib.freenect2_frame_get_status(self._c_object)

    @property
    def format(self):
        return FrameFormat(lib.freenect2_frame_get_format(self._c_object))

    def __repr__(self):
        return (
            'Frame(width={0.width}, height={0.height}, sequence={0.sequence}, '
            'timestamp={0.timestamp}, format={0.format})').format(self)
