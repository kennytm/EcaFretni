#    
#    thread.py ... ARM thread of execution
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

from cpu.arm.status import Status, FloatingPointStatus
from cpu.memory import Memory
from cpu.pointers import StackPointer, Return
from cpu.arm.instruction import Instruction
from copy import deepcopy

class Thread(object):
    '''
    This class represents a thread of execution on ARM. A thread consists of
    registers and a :class:`~cpu.Memory`. 
    
    .. attribute:: r
        
        The general registers r0 to r15 as an array.
    
    .. attribute:: cpsr
    
        The Current Program Status Register.
    
    .. attribute:: spsr
    
        The Saved Program Status Register.
    
    .. attribute:: fpscr
    
        The Floating-point Status and Control Register.

    
    .. attribute:: s
    
        The VFP registers s0 to s31 as an array. These registers hold 32-bit
        integers or IEEE single-precision (binary32) numbers.
    
    .. attribute:: d
    
        The VFP/NEON registers d0 to d31 as an array. These registers hold
        64-bit integers or IEEE double-precision (binary64) numbers.
        
    
    .. attribute:: q
    
        The NEON regiters q0 to q15 as an array. These registers hold 128-bit
        integers.
        
        .. note::
        
            In the actual ARM chip, the :attr:`s`, :attr:`d` and :attr:`q`
            registers share the same memory location. To simplify the
            implementation, this feature will not be replicated.
    
    .. attribute:: memory
    
        The :class:`~cpu.memory.Memory` associated to this thread.
    
    '''

    def __init__(self, ROM, align=4, skipInitialization=False):
        if not skipInitialization:
            self.r = [0] * 16
            self.s = [0] * 32
            self.d = [0] * 32
            self.q = [0] * 16
            self.cpsr = Status()
            self.spsr = Status()
            self.fcpsr = FloatingPointStatus()
            self.memory = Memory(ROM, align)
            self.r[13] = StackPointer(0)
            self.r[14] = Return
        
    def __copy__(self):
        'Create a completely isolated copy (fork) of the current thread.'
        retval = type(self)(None, skipInitialization=True)
        retval.r = deepcopy(self.r)
        retval.s = deepcopy(self.s)
        retval.d = deepcopy(self.d)
        retval.q = deepcopy(self.q)
        retval.cpsr = self.cpsr.__copy__()
        retval.spsr = self.spsr.__copy__()
        retval.fcpsr = self.fcpsr.__copy__()
        retval.memory = self.memory.__copy__()
        return retval
        
    @property 
    def sl(self):
        'This is an alias to ``r[10]``. The acronym means "stack limit".'
        return self.r[10]
    @sl.setter
    def sl(self, value):
        self.r[10] = value
    
    @property
    def fp(self):
        'This is an alias to ``r[11]``. The acronym means "frame pointer".'
        return self.r[11]
    @fp.setter
    def fp(self, value):
        self.r[11] = value
    
    @property
    def ip(self):
        'This is an alias to ``r[12]``. The acronym means "instruction pointer".'
        return self.r[12]
    @ip.setter
    def ip(self, value):
        self.r[12] = value
    
    @property
    def sp(self):
        '''This is an alias to ``r[13]``. The acronym means "stack pointer". The
        value should be a :class:`~cpu.pointers.StackPointer` pointing to the
        top of the stack.'''
        return self.r[13]
    @sp.setter
    def sp(self, value):
        self.r[13] = value
    
    @property
    def lr(self):
        '''This is an alias to ``r[14]``. The acronym means "link register".
        This register often holds the address to the caller, although sometimes
        it is also used as a general-purpose register.'''
        return self.r[14]
    @lr.setter
    def lr(self, value):
        self.r[14] = value
    
    @property
    def pc(self):
        '''This is an alias to ``r[15]``. The acronym means "program counter".
        This is a special register which always points to 4 or 8 bytes after the
        current instruction. Modifying this value will cause the program jump to
        another position.'''
        return self.r[15]
    @pc.setter
    def pc(self, value):
        self.r[15] = value
    
    
    def goto(self, value):
        'Jump to the specific address in the ROM for program execution.'
        pcdiff = 4 if self.cpsr.T else 8
        self.r[15] = value + pcdiff
    
    def advance(self, delta):
        'Advance the :attr:`pc` by *delta* bytes.'
        self.r[15] += delta
        
    @property
    def instructionSet(self):
        '''Get the processor's current instruction set. 
                
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
        '''
        return self.cpsr.instructionSet
        
    def fetch(self):
        '''Fetch an instruction at the current position. Returns a little-endian
        encoded integer that contains the full instruction, and the length of
        the instruction. You need to call :meth:`advance` manually to move the
        program counter.'''
        instrSet = self.cpsr.instructionSet
        thumbMode = instrSet & 1
        pcdiff = 4 if thumbMode else 8
        loc = self.r[15] - pcdiff
        instr = self.memory.get(loc, length=4)
        instrLen = 4
        if thumbMode:
            # Thumb instructions can be 2-byte long.
            instr = (instr & 0xffff) << 16 | instr >> 16
            if instr < (0b11101 << 27):
                instr >>= 16
                instrLen = 2
                
        return Instruction.create(instr, instrLen, instrSet)
                
    def gotoEvent(self, instruction):
        '''This function is called when the
        :meth:`~cpu.arm.instruction.Instruction.run` method caused :attr:`pc` to
        depart from its normal flow.'''
        pass
        
    