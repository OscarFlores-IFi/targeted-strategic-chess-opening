from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension

# Define the Cython extension module
extensions = [Extension("pgn_processor", ["pgn_processor.pyx"])]

# Setup the extension module to be cythonized
setup(
    name='pgn_processor',
    ext_modules=cythonize(extensions),
)
