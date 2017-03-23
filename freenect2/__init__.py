from __future__ import print_function

from contextlib import contextmanager
import enum
from queue import Queue, Empty

import numpy as np
from PIL import Image

from ._freenect2 import lib, ffi

__all__ = (
    'NoDeviceError',
    'NoFrameReceivedError',
    'Device',
    'FrameType',
    'FrameFormat',
    'Frame',
    'Registration',
    'IrCameraParams',
    'ColorCameraParams'
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
    """Raised by :py:class:`.Device` when there is no default device to open."""
    pass

class FrameType(enum.Enum):
    """Available types of frames."""

    #: 1920x1080. BGRX or RGBX
    Color = lib.FRAME_TYPE_COLOR

    #: 512x424 float. Range is [0.0, 65535.0]
    Ir = lib.FRAME_TYPE_IR

    #: 512x424 float, unit: millimeter. Non-positive, NaN, and infinity are
    #: invalid or missing data
    Depth = lib.FRAME_TYPE_DEPTH

class FrameFormat(enum.Enum):
    """Pixel format."""

    #: Invalid format.
    Invalid = lib.FRAME_FORMAT_INVALID

    #: Raw bitstream. 'bytes_per_pixel' defines the number of bytes
    Raw = lib.FRAME_FORMAT_RAW

    #: A 4-byte float per pixel
    Float = lib.FRAME_FORMAT_FLOAT

    #: 4 bytes of B, G, R, and unused per pixel
    BGRX = lib.FRAME_FORMAT_BGRX

    #: 4 bytes of R, G, B, and unused per pixel
    RGBX = lib.FRAME_FORMAT_RGBX

    #: 1 byte of gray per pixel
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

class NoFrameReceivedError(RuntimeError):
    """With the default frame listener this is raised when no frame has been
    received from the device within a set time."""
    pass

class QueueFrameListener(object):
    def __init__(self, maxsize=16):
        self.queue = Queue(maxsize=maxsize)

    def __call__(self, frame_type, frame):
        self.queue.put_nowait((frame_type, frame))

    def get(self, timeout=False):
        return self.queue.get(True, timeout)

class ColorCameraParams(object):
    """
    Color camera intrinsic calibration.

    .. py:attribute:: fx

        Focal length for x-axis (pixels)

    .. py:attribute:: fy

        Focal length for y-axis (pixels)

    .. py:attribute:: cx

        Principal point for x-axis (pixels)

    .. py:attribute:: cy

        Principal point for y-axis (pixels)
    """

class IrCameraParams(object):
    """
    IR/depth camera intrinsic calibration.

    .. py:attribute:: fx

        Focal length for x-axis (pixels)

    .. py:attribute:: fy

        Focal length for y-axis (pixels)

    .. py:attribute:: cx

        Principal point for x-axis (pixels)

    .. py:attribute:: cy

        Principal point for y-axis (pixels)

    .. py:attribute:: k1

        Radial distortion co-efficient, 1st-order

    .. py:attribute:: k2

        Radial distortion co-efficient, 2nd-order

    .. py:attribute:: k3

        Radial distortion co-efficient, 3rd-order

    .. py:attribute:: p1

        Tangential distortion co-efficient

    .. py:attribute:: p2

        Tangential distortion co-efficient
    """

class Device(object):
    """Control a single device.

    If called with no arguments, the default device is opened.

    Raises:
        :py:class:`.NoDeviceError` if there is no default device to open.

    .. py:attribute:: color_camera_params

        (:py:class:`.ColorCameraParams` or None) A structure describing the RGB
        camera factory calibration. Before the :py:func:`.start` is called, this
        is *None* since the device only reports calibration when capture begins.

    .. py:attribute:: ir_camera_params

        (:py:class:`.IrCameraParams` or None) A structure describing the IR
        camera factory calibration. Before the :py:func:`.start` is called, this
        is *None* since the device only reports calibration when capture begins.

    """

    def __init__(self, c_object=None):
        if c_object is None:
            c_object = lib.freenect2_open_default_device(_get_freenect2())
        self._c_object = c_object
        if self._c_object == ffi.NULL:
            raise NoDeviceError()

        self._registration = None

        self._default_listener = QueueFrameListener()
        self.color_frame_listener = self._default_listener
        self.ir_and_depth_frame_listener = self._default_listener

        self.color_camera_params = None
        self.ir_camera_params = None

    def start(self, frame_listener=None):
        """Start depth, IR and RGB streams.

        Args:
            frame_listener (callable or None): if not-None, this is a callable
                which is assigned to both :py:attr:`.color_frame_listener` and
                :py:attr:`.ir_and_depth_frame_listener` before the device is
                started.

        """
        if frame_listener is not None:
            self.color_frame_listener = frame_listener
            self.ir_and_depth_frame_listener = frame_listener
        lib.freenect2_device_start(self._c_object)

        self.color_camera_params = lib.freenect2_device_get_color_camera_params(self._c_object)
        self.ir_camera_params = lib.freenect2_device_get_ir_camera_params(self._c_object)

    def stop(self):
        """Stop any running streams."""
        lib.freenect2_device_stop(self._c_object)

    def close(self):
        """Close the device and free any associated resources."""
        lib.freenect2_device_close(self._c_object)

    def get_next_frame(self, timeout=None):
        """Get the next frame type and frame from the device.

        Args:
            timeout (number or None): If not-None, a positive number of seconds
                to wait for a frame before raising a
                :py:class:`.NoFrameReceivedError` exception.

        Returns:
            A :py:class:`.FrameType`, :py:class:`.Frame` tuple representing the
            type of received frame and the frame itself.

        .. note::

            This method only works if the default listener is being used. That
            is to say that :py:attr:`.color_frame_listener` and
            :py:attr:`.ir_and_depth_frame_listener` have not been changed from
            their default values.

        """
        try:
            frame_type, frame = self._default_listener.get(timeout)
        except Empty:
            raise NoFrameReceivedError()

        return frame_type, frame

    @property
    def registration(self):
        """An instance of :py:class:`.Registration` which can be used to
        undistort the raw depth image and register the RGB image with it.

        """
        if self._registration is None:
            self._registration = Registration(
                self.ir_camera_params, self.color_camera_params)
        return self._registration

    @property
    def color_frame_listener(self):
        """A callable called whenever a new color frame arrives from the
        device. The callable should take two positional arguments, the frame
        type (an instance of :py:class:`.FrameType`) and the frame itself (an
        instance of :py:class:`.Frame`)."""
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
        """A callable called whenever a new IR or depth frame arrives from the
        device. The callable should take two positional arguments, the frame
        type (an instance of :py:class:`.FrameType`) and the frame itself (an
        instance of :py:class:`.Frame`)."""
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
    def running(self, *args, **kwargs):
        """A context manager which can be used to ensure that the device's
        streams are stopped. Any arguments are passed to :py:meth:`.start`.

        .. code::

            from freenect2 import Device

            # Open default device
            device = Device()

            # Start depth and color frames
            with device.running():
                # ... frame listener callbacks will be called ...

            # Device is now stopped

        """
        self.start(*args, **kwargs)
        yield self
        self.stop()

    def __iter__(self):
        def iterator():
            while True:
                yield self.get_next_frame()
        return iterator()

class Frame(object):
    """A single frame received from the device.

    These should not be constructed directly since they are usually created by
    the freenect2 library itself. However you may need to construct "blank"
    frames for use with :py:class:`.Registration`. In which case, you should use
    the :py:meth:`.Frame.create` class method.

    """
    def __init__(self, frame_ref):
        self._c_object = frame_ref

    @classmethod
    def create(self, width, height, bytes_per_pixel):
        """Create a blank frame with the specified width, height and bytes per
        pixel. Memory for the frame is automatically allocated. No other
        attributes are initialised.

        """
        return Frame(lib.freenect2_frame_create(width, height, bytes_per_pixel))

    def to_image(self):
        """Convert the Frame to a PIL :py:class:`Image` instance."""
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
        """Convert the image to a numpy :py:class:`array` instance.

        The memory is not copied so be careful performing any operations which
        modify the contents of the frame.

        """
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
        """Length of a line (in pixels)"""
        return lib.freenect2_frame_get_width(self._c_object)

    @width.setter
    def width(self, value):
        lib.freenect2_frame_set_width(self._c_object, value)

    @property
    def height(self):
        """Number of lines in the frame"""
        return lib.freenect2_frame_get_height(self._c_object)

    @height.setter
    def height(self, value):
        lib.freenect2_frame_set_height(self._c_object, value)

    @property
    def bytes_per_pixel(self):
        """Number of bytes in a pixel. If :py:attr:`.format` is
        :py:attr:`.FrameFormat.Raw`, this is the buffer size."""
        return lib.freenect2_frame_get_bytes_per_pixel(self._c_object)

    @bytes_per_pixel.setter
    def bytes_per_pixel(self, value):
        lib.freenect2_frame_set_bytes_per_pixel(self._c_object, value)

    @property
    def data(self):
        """A buffer object pointing to the raw memory contents of the frame."""
        data_ptr = lib.freenect2_frame_get_data(self._c_object)
        return ffi.buffer(
            data_ptr, self.width * self.height * self.bytes_per_pixel)

    @property
    def timestamp(self):
        """Unit: roughly or exactly 0.1 millisecond"""
        return lib.freenect2_frame_get_timestamp(self._c_object)

    @timestamp.setter
    def timestamp(self, value):
        lib.freenect2_frame_set_timestamp(self._c_object, value)

    @property
    def sequence(self):
        """Increasing frame sequence number"""
        return lib.freenect2_frame_get_sequence(self._c_object)

    @sequence.setter
    def sequence(self, value):
        lib.freenect2_frame_set_sequence(self._c_object, value)

    @property
    def exposure(self):
        """From 0.5 (very bright) to ~60.0 (fully covered)"""
        return lib.freenect2_frame_get_exposure(self._c_object)

    @exposure.setter
    def exposure(self, value):
        lib.freenect2_frame_set_exposure(self._c_object, value)

    @property
    def gain(self):
        """From 1.0 (bright) to 1.5 (covered)"""
        return lib.freenect2_frame_get_gain(self._c_object)

    @gain.setter
    def gain(self, value):
        lib.freenect2_frame_set_gain(self._c_object, value)

    @property
    def gamma(self):
        """From 1.0 (bright) to 6.4 (covered)"""
        return lib.freenect2_frame_get_gamma(self._c_object)

    @gamma.setter
    def gamma(self, value):
        lib.freenect2_frame_set_gamma(self._c_object, value)

    @property
    def status(self):
        """zero if ok; non-zero for errors"""
        return lib.freenect2_frame_get_status(self._c_object)

    @status.setter
    def status(self, value):
        lib.freenect2_frame_set_status(self._c_object, value)

    @property
    def format(self):
        """Byte format. Informative only, doesn't indicate errors. An instance
        of :py:class:`.FrameFormat`."""
        return FrameFormat(lib.freenect2_frame_get_format(self._c_object))

    @format.setter
    def format(self, value):
        lib.freenect2_frame_set_format(self._c_object, value.value)

    def __repr__(self):
        return (
            'Frame(width={0.width}, height={0.height}, sequence={0.sequence}, '
            'timestamp={0.timestamp}, format={0.format})').format(self)

class Registration(object):
    """Information required to undistort raw depth frames and register RGB
    frames onto depth.

    Do not construct this directly. Instead use the
    :py:attr:`.Device.registration` attribute.

    """
    def __init__(self, depth_p, rgb_p):
        self.depth_p = depth_p
        self.rgb_p = rgb_p
        self._c_object = ffi.gc(
            lib.freenect2_registration_create(depth_p, rgb_p),
            lib.freenect2_registration_dispose)

    def apply(self, rgb, depth, enable_filter=True, with_big_depth=False):
        """Take an RGB and Depth image and return tuple with the undistorted
        depth image and color image rectified onto depth.

        Args:
            rgb (:py:class:`.Frame`): RGB frame received from device
            depth (:py:class:`.Frame`): Depth frame received from device
            enable_filter (bool): If true, filter out pixels not visible in
                both cameras.
            with_big_depth (bool): If true, also return a 1920x1082 mapping of
                depth onto the color map. The top and bottom rows are blank.

        Returns:
            A :py:class:`Frame` pair representing the undistorted depth and
            registered RGB frames.

        """
        undistorted = Frame.create(512, 424, 4)
        undistorted.format = depth.format
        registered = Frame.create(512, 424, 4)
        registered.format = rgb.format

        big_depth, big_depth_ref = None, ffi.NULL
        if with_big_depth:
            big_depth = Frame.create(1920, 1082, 4)
            big_depth.format = depth.format
            big_depth_ref = big_depth._c_object

        lib.freenect2_registration_apply(
            self._c_object,
            rgb._c_object, depth._c_object, undistorted._c_object,
            registered._c_object, 1 if enable_filter else 0,
            big_depth_ref
        )

        rvs = [undistorted, registered]
        if with_big_depth:
            rvs.append(big_depth)

        return tuple(rvs)

    def get_points_xyz(self, undistorted, rows, cols):
        """Retrieve real-world co-ordinates corresponding to points in the
        undistorted depth image. Units are millimetres.

        Args:
            undistorted (:py:class:`Frame`): the undistorted depth frame
            rows (numpy array): integer row indices of points in the depth frame
            cols (numpy array): integer column indices of points in the depth
                frame. Must be the same shape as *rows*.

        Returns:
            A three element tuple containing numpy arrays for the x-, y- and
            z-co-ordinates of the points. Each array has the same shape as
            *rows*.
        """
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
        return xs, ys, -zs

    def get_points_xyz_array(self, undistorted):
        """Return a 3D array of x, y, z points for each point in an undistorted
        frame. Invalid points are Nan-ed.

        Args:
            undistorted (:py:class:`.Frame`): the undistorted depth frame

        Returns:
            A 424x512x3 array of 3D points. The last dimension corresponding to
            x, y and z.

        """
        cols, rows = np.meshgrid(
            np.arange(undistorted.width), np.arange(undistorted.height))
        return np.dstack(self.get_points_xyz(undistorted, rows, cols))

    def get_big_points_xyz_array(self, big_depth):
        """Like :py:meth:`.get_points_xyz_array` but operates on the "big" depth
        map which can be returned from :py:meth:`.apply`.

        Args:
            big_depth (:py:class:`.Frame`): big 1920x1082 frame returned from
                :py:meth:`.apply`.

        Returns:
            A 1082x1920x3 array of 3D points. The last dimension corresponding
            to x, y and z.

        """
        points = np.ones((big_depth.height, big_depth.width, 3), dtype=np.float32)
        points[..., 2] = 1e-3 * big_depth.to_array()
        points[..., 0], points[..., 1] = np.meshgrid(
            (np.arange(1920) - self.rgb_p.cx) / self.rgb_p.fx,
            (1080-np.arange(-1, 1081) - self.rgb_p.cy) / self.rgb_p.fy)
        points[..., 0] *= points[..., 2]
        points[..., 1] *= points[..., 2]

        return points

    def write_pcd(self, file_object, undistorted, registered=None):
        """Write depth map and (optionally) RGB data to libpcl-compatible PCD
        format file. If the registered RGB frame is present, each point is
        coloured according to the image otherwise the points are left
        uncoloured.

        .. note::

            Under Python 3 the file object *must* be opened in binary mode.

        Args:
            file_object (file): A file object to write PCD data to
            undistorted (:py:class:`Frame`): the undistorted depth frame
            registered (:py:class:`Frame`): if not-None, the RGB data corresponding to
                the depth frame.
        """
        write_pcd(
            file_object, self.get_points_xyz_array(undistorted), registered)

    def write_big_pcd(self, file_object, big_depth, rgb=None):
        """Write depth map and (optionally) RGB data to libpcl-compatible PCD
        format file. Works like :py:meth:`.write_pcd` except that it works on
        the "big" depth map which can be returned from :py:meth:`apply`. If the
        RGB frame is present, each point is coloured according to the image
        otherwise the points are left uncoloured.

        .. note::

            Under Python 3 the file object *must* be opened in binary mode.

        Args:
            file_object (file): A file object to write PCD data to
            big_depth (:py:class:`Frame`): the 1920x1082 de[th frame
            registered (:py:class:`Frame`): if not-None, the RGB data from the
                color camera
        """
        write_pcd(
            file_object,
            self.get_big_points_xyz_array(big_depth)[1:-1, ...], rgb)

def write_pcd(file_object, points, rgb=None):
    """Write 3d points and (optionally) RGB data to libpcl-compatible PCD
    format file. If the registered RGB frame is present, each point is
    coloured according to the image otherwise the points are left
    uncoloured.

    .. note::

        Under Python 3 the file object *must* be opened in binary mode.

    Args:
        file_object (file): A file object to write PCD data to
        points (array): A NxMx3 array of 3d points.
        rgb (:py:class:`Frame`): if not-None, the RGB frame corresponding to
            the points array. Assumed to be NxM.
    """
    assert len(points.shape) == 3
    xs, ys, zs = points[..., 0], points[..., 1], points[..., 2]
    n_points = int(np.product(points.shape[:-1]))

    file_object.write(b'VERSION .7\n')

    if rgb is None:
        file_object.write(
            b'FIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\n')
        data = np.zeros((n_points, 3), order='C', dtype=np.float32)
        data[:, 0] = xs.flatten()
        data[:, 1] = ys.flatten()
        data[:, 2] = zs.flatten()
    else:
        file_object.write(
            b'FIELDS x y z rgb\nSIZE 4 4 4 4\nTYPE F F F F\nCOUNT 1 1 1 1\n')
        bgrx = rgb.to_array().astype(np.uint32)
        rgbs = (
            bgrx[..., 0] + (bgrx[..., 1] << 8) + (bgrx[..., 2] << 16)
        ).view(np.float32)
        data = np.zeros((n_points, 4), order='C', dtype=np.float32)
        data[:, 0] = xs.flatten()
        data[:, 1] = ys.flatten()
        data[:, 2] = zs.flatten()
        data[:, 3] = rgbs.flatten()

    file_object.write('WIDTH {}\n'.format(points.shape[1]).encode())
    file_object.write('HEIGHT {}\n'.format(points.shape[0]).encode())
    file_object.write(b'VIEWPOINT 0 0 0 1 0 0 0\n')
    file_object.write('POINTS {}\n'.format(n_points).encode())
    file_object.write(b'DATA binary\n')
    file_object.write(data.tobytes())
