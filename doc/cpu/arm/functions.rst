:mod:`~cpu.arm.functions` --- ARM pseudocode functions
======================================================

The ARM reference defines a lot of pseudocode functions in explaining how the
instructions work. This module implements most of them that are relevant.

Auxiliary functions
-------------------
.. autofunction:: cpu.arm.functions.signed

Fixing PC address
-----------------

.. autofunction:: cpu.arm.functions.fixPCAddrBX
.. autofunction:: cpu.arm.functions.fixPCAddrB


Shift and rotate operations
---------------------------

.. autofunction:: cpu.arm.functions.LSL_C
.. autofunction:: cpu.arm.functions.LSL
.. autofunction:: cpu.arm.functions.LSR_C
.. autofunction:: cpu.arm.functions.LSR
.. autofunction:: cpu.arm.functions.ASR_C
.. autofunction:: cpu.arm.functions.ASR
.. autofunction:: cpu.arm.functions.ROR_C
.. autofunction:: cpu.arm.functions.ROR
.. autofunction:: cpu.arm.functions.RRX_C
.. autofunction:: cpu.arm.functions.RRX

Instruction-specified shifts and rotates
----------------------------------------

.. autofunction:: cpu.arm.functions.Shift_C
.. autofunction:: cpu.arm.functions.Shift
.. autofunction:: cpu.arm.functions.DecodeImmShift

.. data:: cpu.arm.functions.SRTYPE_LSL (0)
    cpu.arm.functions.SRTYPE_LSR (1)
    cpu.arm.functions.SRTYPE_ASR (2)
    cpu.arm.functions.SRTYPE_ROR (3)
    cpu.arm.functions.SRTYPE_RRX (4)
    
    The shift types.
    
Expansion of immediates
-----------------------

.. autofunction:: cpu.arm.functions.ThumbExpandImm_C
.. autofunction:: cpu.arm.functions.ThumbExpandImm
.. autofunction:: cpu.arm.functions.ARMExpandImm_C
.. autofunction:: cpu.arm.functions.ARMExpandImm

Addition and subtraction
------------------------

.. autofunction:: cpu.arm.functions.AddWithCarry

