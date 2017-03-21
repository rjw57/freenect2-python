freenect2: Python bindings to libfreenect2
==========================================

.. image:: https://travis-ci.org/rjw57/freenect2-python.svg?branch=master
    :target: https://travis-ci.org/rjw57/freenect2-python

The freenect2 module provides a Python interface to the `libfreenect2
<https://github.com/OpenKinect/libfreenect2>`_ library.  The libfreenect2
library provides a library allowing depth and RGB data to be extracted from a
Kinect for Windows v2 (K4W2) device.

Although a lot of libfreenect2 functionality is exposed, simple "single grab"
usage of freenect2 should be simple. For example, here is how to grab a single
depth frame and save it to a grayscale JPEG:

.. code:: python

    from PIL.ImageMath import eval as im_eval
    from freenect2 import Device, FrameType

    device = Device()
    with device.running():
        for frame_type, frame in device:
            if frame_type is FrameType.Depth:
                # Convert range of depth image to 0->255.
                norm_im = im_eval('convert(I / 16, "L")', I=frame.to_image())
                norm_im.save('depth.jpg')
                break
