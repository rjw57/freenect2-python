from setuptools import setup, find_packages

with open('requirements.txt') as fobj:
    install_requires = fobj.readlines()

setup(
    name='freenect2',
    packages=find_packages(),
    install_requires=install_requires,
    setup_requires=['cffi>=1.0.0'],
    cffi_modules=['freenect2_build.py:ffibuilder'],
)
