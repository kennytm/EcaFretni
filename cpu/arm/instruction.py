#    
#    instruction.py ... ARM instructions
#    Copyright (C) 2011  KennyTM~ <kennytm@gmail.com>
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from collections import Hashable
from abc import ABCMeta, abstractmethod, abstractproperty
from cpu.arm.functions import Shift, Shift_C
from cpu.arm.operand import Constant, Operand

__all__ = ['Instruction', 'Condition']

def _formatShift(shiftType, shiftAmount):
    if shiftType == 4:
        return "rrx"
    else:
        return "{0} {1}".format(("lsl", "lsr", "asr", "ror")[shiftType], shiftAmount.decstr())

class abstractclassmethod(classmethod):
    __isabstractmethod__ = True
    def __init__(self, callable):
        callable.__isabstractmethod__ = True
        super().__init__(callable)

class Instruction(metaclass=ABCMeta):
    '''
    The base class for all ARM and Thumb instructions.
    
    .. attribute:: encoding
    
        The encoding (as a little-endian integer) of this instruction.
    
    .. attribute:: length
    
        The length of this instruction.
    
    .. attribute:: instructionSet
    
        The instruction set of this instruction.
        
        +-------+-----------------+
        | Value | Instruction set |
        +=======+=================+
        | 0     | ARM             |
        +-------+-----------------+
        | 1     | Thumb           |
        +-------+-----------------+
        | 2     | Jazelle         |
        +-------+-----------------+
        | 3     | ThumbEE         |
        +-------+-----------------+
        
    .. attribute:: condition
    
        The :class:`Condition` of this instruction.
        
    .. attribute:: width
    
        The instruction width. This field only affects the disassembly.

        +----------+--------------------+
        | Width    | Meaning            |
        +==========+====================+
        | ``''``   | Default            |
        +----------+--------------------+
        | ``'.n'`` | Force narrow       |
        +----------+--------------------+
        | ``'.w'`` | Force wide         |
        +----------+--------------------+
        
    .. attribute:: shiftType
        shiftAmount
    
        The shift type and amount to be applied to the last operand.
        
        +--------------------------------------------+---------------------------------+
        | Shift type                                 | Meaning                         |
        +============================================+=================================+
        | :const:`~cpu.arm.functions.SRTYPE_LSL` (0) | Left shift                      |
        +--------------------------------------------+---------------------------------+
        | :const:`~cpu.arm.functions.SRTYPE_LSR` (1) | Logical (unsigned) right shift  |
        +--------------------------------------------+---------------------------------+
        | :const:`~cpu.arm.functions.SRTYPE_ASR` (2) | Arithmetic (signed) right shift |
        +--------------------------------------------+---------------------------------+
        | :const:`~cpu.arm.functions.SRTYPE_ROR` (3) | Rotate bits right               |
        +--------------------------------------------+---------------------------------+
        | :const:`~cpu.arm.functions.SRTYPE_RRX` (4) | Rotate bits right with carry    |
        +--------------------------------------------+---------------------------------+
                
    '''
    
    UNCONDITIONAL = False
        
    def __init__(self, encoding, length, instructionSet):
        self.length = length
        self.encoding = encoding
        self.instructionSet = instructionSet
        self.condition = Condition(Condition.AL)
        self.width = ''
        self.shiftType = 0
        self.shiftAmount = Constant(0)


    @classmethod
    def create(cls, encoding, length, instructionSet, forceCondition=15):
        '''Create an instruction using *encoding* with length *length* in
        *instructionSet*.
        
        If the instruction ought to carry a condition (e.g. due to the IT block)
        you could supply a valid condition code in *forceCondition*.'''
        
        isARM = instructionSet == 0
        cond = forceCondition
        if isARM and cond == 15:
            cond = encoding >> 28
            encoding &= 0xfffffff
        
        for sub in cls.__subclasses__():
            if isARM and sub.UNCONDITIONAL != (cond == 15):
                continue
            retval = sub.tryCreate(encoding, length, instructionSet, cond)
            if retval:
                break
        else:
             retval = cls(encoding, length, instructionSet)

        if cond != 15:
            retval.condition = Condition(cond)
        return retval

    @abstractclassmethod
    def tryCreate(cls, encoding, length, instructionSet, condition):
        '''Try to create an instruction with this subclass. If this particular
        subclass cannot handle *encoding*, it should return ``None``. All
        subclasses must override this function.
        
        When this method is called with an ARM instruction, the condition code
        will *not* be included along the *encoding*. If the subclass is an
        unconditional instruction (i.e. the condition code must always be 15),
        the subclass should override the class attribute ``UNCONDITIONAL`` to
        True.'''
        assert False

    @abstractmethod
    def mainOpcode(self):
        "Return the instruction's opcode without conditions."
        return '<unk{0:0{1}x}>'.format(self.encoding, self.length*2)
        
    @property
    def opcode(self):
        '''Return the instruction's opcode (including condition code). 
        
        Subclasses should overload the :meth:`mainOpcode` method to provide the
        actual opcode.'''
        return self.mainOpcode() + str(self.condition) + self.width
        
    def forceWide(self):
        '''Force the ".w" qualifier to show in the disassembly of this
        instruction. Returns ``self``.'''
        self.width = '.w'
        return self
    
    def setShift(self, shiftTypeAndAmount):
        'Set the :attr:`shiftType` and :attr:`shiftAmount`. Returns ``self``.'
        self.shiftType = shiftTypeAndAmount[0]
        shiftAmount = shiftTypeAndAmount[1]
        if not isinstance(shiftAmount, Operand):
            shiftAmount = Constant(shiftAmount)
        self.shiftAmount = shiftAmount
        return self

    def execute(self, thread):
        'Execute the instruction with a *thread*'
        location = thread.pcRaw
        thread.pc = location + self.length
        if self.condition.check(thread.cpsr):
            self.exec(thread)
            if thread.pcRaw != location:
                thread.gotoEvent(self)

        
    @abstractmethod
    def exec(self, thread):
        '''Execute the instruction with a *thread* after passing the conditions.
        
        Subclasses should override this method to provide the actual
        implementation of this instruction.'''
        assert False
    
    @abstractproperty
    def operands(self):
        'Return a list of :class:`~cpu.arm.operand.Operand`\s of the instruction.'
        return []
    
    def applyShift(self, thread, value, carry):
        'Apply shift to an integer. Return the shifted value.'
        return Shift(0xffffffff, value, self.shiftType, self.shiftAmount.get(thread), carry)
    
    def applyShift_C(self, thread, value, carry):
        'Apply shift to an integer. Return the shifted value and carry.'        
        return Shift_C(0xffffffff, value, self.shiftType, self.shiftAmount.get(thread), carry)

    def __str__(self):
        'Disassemble this instruction.'
        opcode = self.opcode
        operands = ', '.join(map(str, self.operands))
        if self.shiftAmount:
            operands += _formatShift(self.shiftType, self.shiftAmount)
        return '{0}\t{1}'.format(opcode, operands)
        


_condcodes = ['eq','ne','cs','cc','mi','pl','vs','vc','hi','ls','ge','gt','le','','xx']
_condchecks = [
    lambda status: status.Z,
    lambda status: not status.Z,
    lambda status: status.C,
    lambda status: not status.C,
    lambda status: status.N,
    lambda status: not status.N,
    lambda status: status.V,
    lambda status: not status.V,
    lambda status: status.C and not status.Z,
    lambda status: not status.C or status.Z,
    lambda status: bool(status.N) == bool(status.V),
    lambda status: bool(status.N) != bool(status.V),
    lambda status: not status.Z and bool(status.N) == bool(status.V),
    lambda status: status.Z or bool(status.N) != bool(status.V),
    lambda status: True,
    lambda status: False,
]


class Condition(Hashable):
    '''
    The condition code of an instruction. The code is a special feature of the
    ARM instruction set to reduce the number of branches. An instruction is
    executed only when the specified condition is fulfilled. 
    
    .. data:: EQ
        NE
        CS
        CC
        MI
        PL
        VS
        VC
        HI
        LS
        GE
        GT
        GT
        LE
        AL
        NV
        
        These class constants specify the raw value of the condition codes.
        
        +-------------+----------------+-----------------------------------------------+
        | Code        | Condition      | Meaning                                       |
        +=============+================+===============================================+
        | ``EQ`` (0)  | ``Z == 1``     | Equal (``==``)                                |
        +-------------+----------------+-----------------------------------------------+
        | ``NE`` (1)  | ``Z == 0``     | Not equal (``!=``)                            |
        +-------------+----------------+-----------------------------------------------+
        | ``CS`` (2)  | ``C == 1``     | Carry set / unsigned higher or same (``!<``)  |
        +-------------+----------------+-----------------------------------------------+
        | ``CC`` (3)  | ``C == 0``     | Carry clear / unsigned lower (``<``)          |
        +-------------+----------------+-----------------------------------------------+
        | ``MI`` (4)  | ``N == 1``     | Negative (``<``)                              |
        +-------------+----------------+-----------------------------------------------+
        | ``PL`` (5)  | ``N == 0``     | Nonnegative (``!<``)                          |
        +-------------+----------------+-----------------------------------------------+
        | ``VS`` (6)  | ``V == 1``     | Overflow (``!<>=``)                           |
        +-------------+----------------+-----------------------------------------------+
        | ``VC`` (7)  | ``V == 0``     | No overflow (``<>=``)                         |
        +-------------+----------------+-----------------------------------------------+
        | ``HI`` (8)  | ``C && !Z``    | Unsigned higher (``!<=``)                     |
        +-------------+----------------+-----------------------------------------------+
        | ``LS`` (9)  | ``!C || Z``    | Unsigned lower or same (``<=``)               |
        +-------------+----------------+-----------------------------------------------+
        | ``GE`` (10) | ``N == V``     | Signed greater than or equal (``>=``)         |
        +-------------+----------------+-----------------------------------------------+
        | ``LT`` (11) | ``N != V``     | Signed less than (``!>=``)                    |
        +-------------+----------------+-----------------------------------------------+
        | ``GT`` (12) | ``!Z && N==V`` | Signed greater than (``>``)                   |
        +-------------+----------------+-----------------------------------------------+
        | ``LE`` (13) | ``Z || N!=V``  | Signed less than or equal (``!>``)            |
        +-------------+----------------+-----------------------------------------------+
        | ``AL`` (14) | ``true``       | Always true                                   |
        +-------------+----------------+-----------------------------------------------+
        | ``NV`` (15) | ``false``      | Always false (not ARM standard)               |
        +-------------+----------------+-----------------------------------------------+

    .. attribute:: condition
    
        The condition code of this instance.

    '''

    (EQ, NE, CS, CC, MI, PL, VS, VC, HI, LS, GE, GT, GT, LE, AL, NV) = range(16)    
    
    def __init__(self, condition):
        self.condition = condition
    
    @property
    def inverse(self):
        'Get the inverse (negation) of this condition.'
        return Condition(self.condition ^ 1)
        
    def __str__(self):
        return _condcodes[self.condition]
    
    def __eq__(self, condition):
        'Check if two conditions are the same.'
        return self.condition == other.condition

    def __hash__(self):
        'Get the hash value of this condition.'
        return hash(self.condition)

    def check(self, status):
        '''Check if the *status* of class :class:`~cpu.arm.status.Status`
        satisfies this condition.'''
        cond = self.condition
        return _condchecks[cond](status)






