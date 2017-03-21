libfreenect2 Python bindings
============================

.. toctree::
    :maxdepth: 2
    :caption: Contents:

The :py:mod:`freenect2` module provides a Python interface to the `libfreenect2
<https://github.com/OpenKinect/libfreenect2>`_ library. The libfreenect2 library
provides a library allowing depth and RGB data to be extracted from a Kinect for
Windows v2 (K4W2) device.

The library is intended to provide an easy to use Pythonic interface to
libfreenect2. As an example of library usage, here is a simple infrared (IR)
camera which can be used to capture an image from the Kinect's build in IR
camera:

.. literalinclude:: ../examples/ir_camera.py
    :language: python

The library also supports extracting real-world 3D co-ordinates from the depth
maps and saving `libpcl <http://pointclouds.org/>`_-compatible PCD files:

.. literalinclude:: ../examples/dump_pcd.py
    :language: python

Installation
============

libfreenect2 must be installed prior to building this module. See the
`installation instructions
<https://github.com/OpenKinect/libfreenect2/blob/master/README.md#installation>`_
provided by libfreenect2. The following is a brief summary of the required
actions:

.. code:: console

    $ git clone https://github.com/OpenKinect/libfreenect2
    ...
    $ cd libfreenect2; mkdir build; cd build
    $ cmake -DCMAKE_INSTALL_PREFIX=$HOME/.local .. && make all install
    ...
    $ export PKG_CONFIG_PATH=$HOME/.local/lib/pkgconfig
    $ pip install --user freenect2

pkg-config errors
-----------------

The libfreenect2 library uses pkg-config to record where it is installed on the
system. If you install libfreenect2 manually as outlined above you will need to
set the `PKG_CONFIG_PATH` environment variable.

Reference
=========

.. automodule:: freenect2
    :members:
