from __future__ import print_function

from contextlib import contextmanager
import enum

import numpy as np
from PIL import Image

from ._freenect2 import lib, ffi

__all__ = (
    'NoDeviceError', 'FrameType', 'FrameFormat', 'Device', 'Frame',
    'Registration',
)

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

        self._color_frame_listener = (None, None, None)
        self._ir_and_depth_frame_listener = (None, None, None)
        self._registration = None

    def start(self):
        lib.freenect2_device_start(self._c_object)

    def stop(self):
        lib.freenect2_device_stop(self._c_object)

    def close(self):
        lib.freenect2_device_close(self._c_object)

    @property
    def registration(self):
        if self._registration is None:
            self._registration = Registration(
                self.ir_camera_params, self.color_camera_params)
        return self._registration

    @property
    def ir_camera_params(self):
        return lib.freenect2_device_get_ir_camera_params(self._c_object)

    @property
    def color_camera_params(self):
        return lib.freenect2_device_get_color_camera_params(self._c_object)

    @property
    def color_frame_listener(self):
        return self._color_frame_listener[0]

    @color_frame_listener.setter
    def color_frame_listener(self, value):
        if value is None:
            self._color_frame_listener = (None, None, None)
            return
        handle, fl = _callable_to_frame_listener(value)
        lib.freenect2_device_set_color_frame_listener(self._c_object, fl)
        self._color_frame_listener = value, handle, fl

    @property
    def ir_and_depth_frame_listener(self):
        return self._ir_and_depth_frame_listener[0]

    @ir_and_depth_frame_listener.setter
    def ir_and_depth_frame_listener(self, value):
        if value is None:
            self._ir_and_depth_frame_listener = (None, None, None)
            return
        handle, fl = _callable_to_frame_listener(value)
        lib.freenect2_device_set_ir_and_depth_frame_listener(self._c_object, fl)
        self._ir_and_depth_frame_listener = value, handle, fl

    @contextmanager
    def running(self):
        self.start()
        yield self
        self.stop()

class Frame(object):
    def __init__(self, frame_ref):
        self._c_object = frame_ref

    @classmethod
    def create(self, width, height, bytes_per_pixel):
        return Frame(lib.freenect2_frame_create(width, height, bytes_per_pixel))

    def to_image(self):
        """Convert the Frame to a PIL image."""
        if self.format is FrameFormat.BGRX:
            return Image.frombuffer(
                'RGB', (self.width, self.height), self.data, 'raw', 'BGRX')
        elif self.format is FrameFormat.RGBX:
            return Image.frombuffer(
                'RGB', (self.width, self.height), self.data, 'raw', 'RGBX')
        elif self.format is FrameFormat.Gray:
            return Image.frombuffer(
                'L', (self.width, self.height), self.data, 'raw', 'L')
        elif self.format is FrameFormat.Float:
            return Image.frombuffer(
                'F', (self.width, self.height), self.data, 'raw', 'F')
        else:
            raise NotImplementedError()

    def to_array(self):
        """Convert the image to a numpy array."""
        if self.format is FrameFormat.BGRX or self.format is FrameFormat.RGBX:
            return np.frombuffer(
                self.data, dtype='uint8').reshape(
                    (self.height, self.width, 4), order='C')
        elif self.format is FrameFormat.Gray:
            return np.frombuffer(
                self.data, dtype='uint8').reshape(
                    (self.height, self.width), order='C')
        elif self.format is FrameFormat.Float:
            return np.frombuffer(
                self.data, dtype='float32').reshape(
                    (self.height, self.width), order='C')
        else:
            raise NotImplementedError()

    @property
    def width(self):
        return lib.freenect2_frame_get_width(self._c_object)

    @width.setter
    def width(self, value):
        lib.freenect2_frame_set_width(self._c_object, value)

    @property
    def height(self):
        return lib.freenect2_frame_get_height(self._c_object)

    @height.setter
    def height(self, value):
        lib.freenect2_frame_set_height(self._c_object, value)

    @property
    def bytes_per_pixel(self):
        return lib.freenect2_frame_get_bytes_per_pixel(self._c_object)

    @bytes_per_pixel.setter
    def bytes_per_pixel(self, value):
        lib.freenect2_frame_set_bytes_per_pixel(self._c_object, value)

    @property
    def data(self):
        data_ptr = lib.freenect2_frame_get_data(self._c_object)
        return ffi.buffer(
            data_ptr, self.width * self.height * self.bytes_per_pixel)

    @property
    def timestamp(self):
        return lib.freenect2_frame_get_timestamp(self._c_object)

    @timestamp.setter
    def timestamp(self, value):
        lib.freenect2_frame_set_timestamp(self._c_object, value)

    @property
    def sequence(self):
        return lib.freenect2_frame_get_sequence(self._c_object)

    @sequence.setter
    def sequence(self, value):
        lib.freenect2_frame_set_sequence(self._c_object, value)

    @property
    def exposure(self):
        return lib.freenect2_frame_get_exposure(self._c_object)

    @exposure.setter
    def exposure(self, value):
        lib.freenect2_frame_set_exposure(self._c_object, value)

    @property
    def gain(self):
        return lib.freenect2_frame_get_gain(self._c_object)

    @gain.setter
    def gain(self, value):
        lib.freenect2_frame_set_gain(self._c_object, value)

    @property
    def gamma(self):
        return lib.freenect2_frame_get_gamma(self._c_object)

    @gamma.setter
    def gamma(self, value):
        lib.freenect2_frame_set_gamma(self._c_object, value)

    @property
    def status(self):
        return lib.freenect2_frame_get_status(self._c_object)

    @status.setter
    def status(self, value):
        lib.freenect2_frame_set_status(self._c_object, value)

    @property
    def format(self):
        return FrameFormat(lib.freenect2_frame_get_format(self._c_object))

    @format.setter
    def format(self, value):
        lib.freenect2_frame_set_format(self._c_object, value.value)

    def __repr__(self):
        return (
            'Frame(width={0.width}, height={0.height}, sequence={0.sequence}, '
            'timestamp={0.timestamp}, format={0.format})').format(self)

class Registration(object):
    def __init__(self, depth_p, rgb_p):
        self._c_object = ffi.gc(
            lib.freenect2_registration_create(depth_p, rgb_p),
            lib.freenect2_registration_dispose)

    def apply(self, rgb, depth, enable_filter=True):
        """Take an RGB and Depth image and return tuple with the undistorted
        depth image and color image rectified onto depth. If enable_filter is
        True, pixels not visible to both cameras are filtered out.

        """
        undistorted = Frame.create(512, 424, 4)
        undistorted.format = depth.format
        registered = Frame.create(512, 424, 4)
        registered.format = rgb.format
        lib.freenect2_registration_apply(
            self._c_object,
            rgb._c_object, depth._c_object, undistorted._c_object,
            registered._c_object, 1 if enable_filter else 0
        )
        return undistorted, registered

    def get_points_xyz(self, undistorted, rows, cols):
        rows = np.atleast_1d(rows).astype(np.int32)
        cols = np.atleast_1d(cols).astype(np.int32)
        assert rows.shape == cols.shape
        xs = np.ones(rows.shape, dtype=np.float32)
        ys = np.ones(rows.shape, dtype=np.float32)
        zs = np.ones(rows.shape, dtype=np.float32)
        lib.freenect2_registration_get_points_xyz(
            self._c_object, undistorted._c_object,
            ffi.cast('int32_t*', rows.ctypes.data),
            ffi.cast('int32_t*', cols.ctypes.data),
            int(np.product(rows.shape)),
            ffi.cast('float*', xs.ctypes.data),
            ffi.cast('float*', ys.ctypes.data),
            ffi.cast('float*', zs.ctypes.data)
        )
        return xs, ys, zs

    def write_pcd(self, file_object, undistorted, registered=None):
        undistorted_array = undistorted.to_array()
        rows, cols = np.nonzero(undistorted_array)
        xs, ys, zs = self.get_points_xyz(undistorted, rows, cols)

        print('VERSION .7', file=file_object)

        if registered is None:
            print('FIELDS x y z', file=file_object)
            print('SIZE 4 4 4', file=file_object)
            print('TYPE F F F', file=file_object)
            print('COUNT 1 1 1', file=file_object)
            data = np.vstack((-xs, -ys, -zs)).T
        else:
            print('FIELDS x y z rgb', file=file_object)
            print('SIZE 4 4 4 4', file=file_object)
            print('TYPE F F F I', file=file_object)
            print('COUNT 1 1 1 1', file=file_object)
            bgrx = (registered.to_array()[rows, cols, ...]).astype(np.uint32)
            rgbs = bgrx[:, 0] + (bgrx[:, 1] << 8) + (bgrx[:, 2] << 16)
            data = np.vstack((-xs, -ys, -zs, rgbs)).T

        print('WIDTH {}'.format(xs.shape[0]), file=file_object)
        print('HEIGHT 1', file=file_object)
        print('VIEWPOINT 0 0 0 1 0 0 0', file=file_object)
        print('POINTS {}'.format(xs.shape[0]), file=file_object)
        print('DATA ascii', file=file_object)

        assert data.shape[0] == xs.shape[0]

        for row in data:
            print(' '.join([str(f) for f in row]), file=file_object)
