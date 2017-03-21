freenect2: Python bindings to libfreenect2
==========================================

.. image:: https://travis-ci.org/rjw57/freenect2-python.svg?branch=master
    :target: https://travis-ci.org/rjw57/freenect2-python
.. image:: https://zenodo.org/badge/85711795.svg
    :target: https://zenodo.org/badge/latestdoi/85711795

The freenect2 module provides a Python interface to the `libfreenect2
<https://github.com/OpenKinect/libfreenect2>`_ library.  The libfreenect2
library provides a library allowing depth and RGB data to be extracted from a
Kinect for Windows v2 (K4W2) device.

If using this library in an academic context, please use the DOI linked above.

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

Getting started
---------------

Installation instructions and reference documentation are available on the
associated `documentation <https://rjw57.github.io/freenect2-python/>`_ pages.

