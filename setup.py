import os
from setuptools import setup, find_packages

this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, 'requirements.txt')) as fobj:
    install_requires = fobj.readlines()

setup(
    name='freenect2',
    description='Python bindings for the libfreenect2 Kinect for Windows driver',
    version='0.2.3',
    author='Rich Wareham',
    author_email='rich.freenect2@richwareham.com',
    url='https://github.com/rjw57/freenect2-python',
    packages=find_packages(),
    install_requires=install_requires,
    setup_requires=['cffi>=1.0.0'],
    cffi_modules=['binding/freenect2_build.py:ffibuilder'],
)
