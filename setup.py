import os
from setuptools import setup, find_packages

this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, 'requirements.txt')) as fobj:
    install_requires = fobj.readlines()

setup(
    name='freenect2',
    packages=find_packages(),
    install_requires=install_requires,
    setup_requires=['cffi>=1.0.0'],
    cffi_modules=['binding/freenect2_build.py:ffibuilder'],
)
