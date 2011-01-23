:mod:`cpu` --- CPU emulator
===========================

This package contains modules for emulating the CPU and run some instructions.
Note that the purpose of this package is to allow some simple dynamic analysis
without hooking to a device, but *not* act as a full-featured emulator that can
run and debug programs smoothly. Please consider using dedicated emulator
library such as `PyQemu <http://pypi.python.org/pypi/PyQemu/>`_ for the latter
purpose.

.. toctree::
    :glob:
    
    cpu/*
