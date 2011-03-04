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
    'This class encapsulates a constant (a.k.a. immediate value).'
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

    
class Register(MutableOperand):
    'This class encapsulates a generic register (r0 to r15).'
    def __init__(self, regnum):
        self.rnum = regnum
    def get(self, thread):
        return thread.r[self.rnum]
    def set(self, thread, value):
        thread.r[self.rnum] = value
    def __str__(self):
        rnum = self.rnum
        if rnum < 13:
            return 'r{0}'.format(rnum)
        else:
            return ('sp','lr','pc')[rnum-13]
    def __eq__(self, other):
        return isinstance(other, type(self)) and self.rnum == other.rnum
    def __hash__(self):
        return hash(self.rnum)


class SRegister(MutableOperand):
    'This class encapsulates the 32-bit VFP registers (s0 to s31).'
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
    'This class encapsulates the 64-bit VFP/NEON registers (d0 to d31).'
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
    'This class encapsulates the 128-bit NEON registers (q0 to q15).'
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


#class Relative(Operand):
#    'This class represents relative operands, i.e. the sum of two values.'
#    def __init__(self, base, offset):
#        assert isinstance(base, Operand)
#        assert isinstance(offset, Operand)
#        self.base = base
#        self.offset = offset
#    def get(self, thread):
#        return self.base.get(thread) + self.offset.get(thread)
#    def __str__(self):
#        return '{0}, {1}'.format(self.base, self.offset)
#    def __eq__(self, other):
#        return isinstance(other, type(self)) and self.base == other.base and self.offset == other.offset
#    def __hash__(self):
#        return hash((self.base, self.offset))

