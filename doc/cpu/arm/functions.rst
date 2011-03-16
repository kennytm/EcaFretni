:mod:`~cpu.arm.functions` --- ARM pseudocode functions
======================================================

The ARM reference defines a lot of pseudocode functions in explaining how the
instructions work. This module implements most of them that are relevant.

Auxiliary functions
-------------------
.. autofunction:: cpu.arm.functions.signed

.. data:: cpu.arm.functions.REG_SP (13)
    cpu.arm.functions.REG_LR (14)
    cpu.arm.functions.REG_PC (15)
    
    Special register names.

.. data:: cpu.arm.functions.COND_NONE (15)

    The condition code representing "no condition". Equivalent to
    :const:`cpu.arm.instruction.Condition.NV`.


.. (sect A2.2.1)

Integer arithmetic
------------------

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

.. autofunction:: cpu.arm.functions.AddWithCarry


.. (sect 2.3.1)

Fixing PC address
-----------------

.. autofunction:: cpu.arm.functions.fixPCAddrBX
.. autofunction:: cpu.arm.functions.fixPCAddrB
.. autofunction:: cpu.arm.functions.fixPCAddrLoad
.. autofunction:: cpu.arm.functions.fixPCAddrALU



.. (sect A2.5.2)

ITSTATE operations
------------------

.. autofunction:: cpu.arm.functions.ITAdvance



.. (sect A5.2.4 & A6.3.2)

Expansion of immediates
-----------------------

.. autofunction:: cpu.arm.functions.ThumbExpandImm_C
.. autofunction:: cpu.arm.functions.ThumbExpandImm
.. autofunction:: cpu.arm.functions.ARMExpandImm_C
.. autofunction:: cpu.arm.functions.ARMExpandImm



.. (sect A8.4.3)

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

