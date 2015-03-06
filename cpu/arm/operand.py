#
#    operand.py ... Special operands
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


from abc import ABCMeta, abstractmethod
from cpu.arm.functions import REG_SP, REG_LR, REG_PC, Shift, fixPCAddrLoad
from collections import defaultdict

class Operand(metaclass=ABCMeta):
    '''This class represents an operand. An operand is an argument to an
    instruction, e.g. a constant or a register.'''

    @abstractmethod
    def get(self, thread):
        'Get the value of this operand from a :class:`~cpu.arm.thread.Thread`.'

    @abstractmethod
    def __str__(self):
        '''Get the string representation (in hexadecimal) of this operand. It is
        only used for disassembling.'''

    def decstr(self):
        '''Get the string representation (in decimal) of this operand. It is
        only used for disassembling.

        By default implementation will make it equivalent to ``str(self)``.'''
        return str(self)


class MutableOperand(Operand):
    '''This class represents a mutable operand, where the content of this
    operand can be modified.'''
    @abstractmethod
    def set(self, thread, value):
        'Set the value referred by this operand.'


class Constant(Operand):
    '''This class encapsulates a constant (a.k.a. immediate value).

    .. attribute:: imm

        The value of this constant.
    '''
    def __init__(self, imm):
        self.imm = imm
    def get(self, thread):
        return self.imm
    def __str__(self):
        return '#0x{0:x}'.format(self.imm)
    def decstr(self):
        return '#{0}'.format(self.imm)
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.imm == other.imm
    def __hash__(self):
        return hash(self.imm)
    def __bool__(self):
        return not not self.imm


class PCRelative(Operand):
    '''This class encapsulates a pc-relative offset.

    .. attribute:: delta

        The relative offset from pc.
    '''
    def __init__(self, delta):
        self.delta = delta
    def get(self, thread):
        return thread.pc + self.delta
    def __str__(self):
        return 'pc{0:+#x}'.format(self.delta)
    def decstr(self):
        return 'pc{0:+}'.format(self.delta)
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.delta == other.delta
    def __hash__(self):
        return hash(self.delta)



_register_names = {12: 'ip', REG_SP: 'sp', REG_LR: 'lr', REG_PC: 'pc'}

class Register(MutableOperand):
    '''This class encapsulates a generic register (r0 to r15).

    .. attribute:: rnum

        The register number.
    '''
    def __init__(self, regnum):
        self.rnum = regnum
    def get(self, thread):
        return thread.r[self.rnum]
    def set(self, thread, value):
        thread.r[self.rnum] = value
    def __str__(self):
        rnum = self.rnum
        if rnum in _register_names:
            return _register_names[rnum]
        else:
            return 'r{0}'.format(rnum)
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.rnum == other.rnum
    def __hash__(self):
        return hash(self.rnum)


class SRegister(MutableOperand):
    '''This class encapsulates the 32-bit VFP registers (s0 to s31).

    .. attribute:: snum

        The register number.
    '''
    def __init__(self, regnum):
        self.snum = regnum
    def get(self, thread):
        return thread.s[self.snum]
    def set(self, thread, value):
        thread.s[self.snum] = value
    def __str__(self):
        return 's{0}'.format(self.snum)
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.snum == other.snum
    def __hash__(self):
        return hash(self.snum)


class DRegister(MutableOperand):
    '''This class encapsulates the 64-bit VFP/NEON registers (d0 to d31).

    .. attribute:: dnum

        The register number.
    '''
    def __init__(self, regnum):
        self.dnum = regnum
    def get(self, thread):
        return thread.d[self.dnum]
    def set(self, thread, value):
        thread.d[self.dnum] = value
    def __str__(self):
        return 'd{0}'.format(self.dnum)
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.dnum == other.dnum
    def __hash__(self):
        return hash(self.dnum)


class QRegister(MutableOperand):
    '''This class encapsulates the 128-bit NEON registers (q0 to q15).

    .. attribute:: qnum

        The register number.
    '''
    def __init__(self, regnum):
        self.qnum = regnum
    def get(self, thread):
        return thread.q[self.qnum]
    def set(self, thread, value):
        thread.q[self.qnum] = value
    def __str__(self):
        return 'q{0}'.format(self.qnum)
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.qnum == other.qnum
    def __hash__(self):
        return hash(self.qnum)


_shift_names = ('lsl', 'lsr', 'asr', 'ror', 'rrx')

class Indirect(MutableOperand):
    '''
    The class represents an indirect operand. An indirect operand can be any of
    the followings:

    * ``[Register, \xb1Operand]``
    * ``[Register], \xb1Operand``
    * ``[Register, \xb1Operand]!``
    * ``[Register, \xb1Operand, shift]``

    * ``[Register, \xb1Operand, shift]!``

    .. attribute:: register

        The primary :class:`Register` to offset and write back to.

    .. attribute:: offset

        An :class:`Operand` to offset the register.

    .. attribute:: positive

        Whether the offset should be added or subtracted.

    .. attribute:: writeBack

        Whether to update the register with the offset when dereferenced.

    .. attribute:: index

        Whether the write back should be done as pre-index (``[rN, x]``) or not
        (``[rN], x``).

    .. attribute:: shifType
        shiftAmount

        The shift applied to the offset.
    '''

    def __init__(self, register, offset, positive=True, writeBack=False, index=True, shiftType=0, shiftAmount=0):
        self.register = register
        self.offset = offset
        self.positive = positive
        self.writeBack = writeBack
        self.index = index
        self.shiftType = shiftType
        self.shiftAmount = shiftAmount

    def deref(self, thread, align=~0):
        'Dereference this operand, and write back the offset value when needed.'
        reg = self.register
        base = reg.get(thread) & align
        offset = Shift(0xffffffff, self.offset.get(thread), self.shiftType, self.shiftAmount, thread.cpsr.C)
        offsetAddr = base + offset if self.positive else base - offset
        addr = offsetAddr if self.index else base
        if self.writeBack:
            reg.set(thread, offsetAddr)
        return addr

    def get(self, thread, length=4, align=~0):
        '''Get the value of this operand from a :class:`~cpu.arm.thread.Thread`.
        with an optional number of bytes and alignment (as ``~(nbytes-1)``).'''
        addr = self.deref(thread, align)
        return thread.memory.get(addr, length)

    def set(self, thread, value, length=4):
        '''Set the value referred by this operand, with an optional number of
        bytes.'''
        addr = self.deref(thread)
        thread.memory.set(addr, value & ((1 << (length*8)) - 1), length)

    def __str__(self):
        offset = self.offset
        sign = '' if self.positive else '-'
        if isinstance(offset, Constant):
            offsetStr = ', #{0}{1:#x}'.format(sign, offset.imm)
        else:
            offsetStr = ', {0}{1}'.format(sign, str(offset))

        (shiftType, shiftAmount) = (self.shiftType, self.shiftAmount)
        if shiftType or shiftAmount:
            offsetStr += ', {0} #{1}'.format(_shift_names[shiftType], shiftAmount)

        if offsetStr == ', #0x0':
            offsetStr = ''

        if not self.index:
            formatStr = '[{0}]{1}'
        elif self.writeBack:
            formatStr = '[{0}{1}]!'
        else:
            formatStr = '[{0}{1}]'

        return formatStr.format(self.register, offsetStr)

    def _toTuple(self):
        return (self.rnum, self.offset, self.positive, self.writeBack, self.index, self.shiftType, self.shiftAmount)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self._toTuple() == other._toTuple()

    def __hash__(self):
        return hash(self._toTuple())


class RegisterList(MutableOperand):
    '''
    The class represents an register list structure used in the ``stm`` and
    ``ldm`` instructions.

    .. attribute:: registers

        The list of :class:`Register`\s included in this list.

    '''
    def __init__(self, *rnums):
        self.registers = tuple(map(Register, sorted(rnums)))

    def get(self, thread):
        return (rn.get(thread) for rn in self.registers)

    def set(self, thread, values):
        for rn, val in zip(self.registers, values):
            if rn.rnum == REG_PC:
                (val, thread.cpsr.T) = fixPCAddrLoad(val, thread.cpsr.T)
            rn.set(thread, val)
            if rn.rnum == REG_PC:
                thread.adjustPcOffset()

    def __str__(self):
        def getRegRange(regs):
            it = iter(regs)
            firstR = next(it)
            lastR = firstR
            for r in it:
                rnum = r.rnum
                if rnum in _register_names or rnum - lastR.rnum > 1:
                    yield (firstR, lastR)
                    firstR = r
                lastR = r
            yield (firstR, lastR)

        def stringify(regs):
            for firstR, lastR in getRegRange(regs):
                if firstR == lastR:
                    yield str(firstR)
                else:
                    yield '{0}-{1}'.format(firstR, lastR)

        return '{' + ', '.join(stringify(self.registers)) + '}'

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.registers == other.registers

    def __hash__(self):
        return hash(self.registers)

    def __len__(self):
        'Return the length of registers.'
        return len(self.registers)

    def __iter__(self):
        'Return an iterator of the registers.'
        return iter(self.registers)


