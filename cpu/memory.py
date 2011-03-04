#    
#    memory.py ... Memory
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


'''
This module defines classes for memory management. In EcaFretni's emulator, the
memory is separated into 3 isolated regions: The RAM and ROM, the stack and the
heap.

The ROM is an immutable memory-mapped object. It often refers to the code and
data of the running executable. The RAM is a copy-on-write layer built on top of
the ROM. The RAM have finite size and can be randomly accessed. The pointers are
simple integers.

The stack is a mutable deque of pointer-sized objects. It models an infinitely
long linear memory structure extends to both directions. Temporary objects are
pushed and popped on it. The stack has infinite size and can be randomly
accessed. The pointers are :class:`~cpu.pointers.StackPointer`\s.

The heap is a mutable pool of objects. It models an infinitely large structure
with no order. Long-living objects are stored on it. The heap has infinite size
and every heap object do not overlap with each other. The pointers are
:class:`~cpu.pointers.HeapPointer`\s.

'''
from collections import deque
from struct import Struct
from itertools import repeat

_strus = (None, Struct('<B'), Struct('<H'), None, Struct('<I'), None, None, None, Struct('<Q'))


def decompose(obj, offset, length):
    '''Decompose *obj* into bytes in little-endian, then return the value at
    *offset* with length *length*. For example,
    
    >>> decompose(0x12345678, 2, 1)
    0x34
    
    This function is defined for integers only, but other classes could declare
    their ``decompose`` method to make this work too. The signature must be:: 
    
        def decompose(self, offset, length):
            ...
    
    and return an integer with *length* bytes.
    '''
    if isinstance(obj, int):
        rightShift = offset * 8
        mask = (1 << (length * 8)) - 1
        return (obj >> rightShift) & mask
    else:
        return obj.decompose(offset, length)

def replaceDecomposed(obj, offset, value, length):
    '''Decompose *obj* into bytes in little-endian, then replace the value at
    *offset* with length *length* by *value*. Return the new object containing
    the change as a result. For example,
    
    >>> replaceDecomposed(0x12345678, 2, 0xff, 1)
    0x12ff5678
    
    It is possible that *obj* be mutated when calling this function.
    
    This function is defined for integers only, but other classes could declare
    their ``replaceDecomposed`` method to make this work too. The signature must
    be:: 
    
        def replaceDecomposed(self, offset, value, length):
            ...
    '''
    if isinstance(obj, int):
        rightShift = offset * 8
        mask = (1 << (length * 8)) - 1
        obj &= ~(mask << rightShift)
        obj |= value << rightShift
        return obj
    else:
        return obj.replaceDecomposed(offset, value, length)


class SimulatedROM(object):
    '''
    This class represents a simulated ROM backed by a buffer. This ROM only 
    contains one memory mapped region. This class is intended for debug purpose
    only.
    
    .. attribute:: vmaddr
    
        The start VM address
        
    .. attribute:: content
    
        The bytes supporting this ROM.
    
    '''
    def __init__(self, content, vmaddr=0):
        self.content = content
        self.vmaddr = vmaddr
        
    def derefBytes(self, vmaddr, length):
        'Return the slice of content at *vmaddr* with length *length*.'
        offset = vmaddr - self.vmaddr
        return self.content[offset:offset+length]


class RAM(object):
    '''
    The class represents a RAM.
    
    .. attribute:: ROM
    
        The ROM it is operating on. This instance must be able to respond to the
        ``derefBytes`` function for dereferencing with signature::
        
            def derefBytes(self, vmaddr, length):
                ...
        
        where *vmaddr* is the VM address to dereference, and *length* is the
        number of bytes to get. It should return a buffer object.
    
    .. attribute:: align
    
        The native pointer width. 
        
    '''
    
    def __init__(self, ROM, align=4):
        assert hasattr(ROM, 'derefBytes')
        self._cowlayer = {}
        self.ROM = ROM
        self.align = align
        self._rightShift = (align-1).bit_length()
        
    def get(self, vmaddr, length=0):
        'Get an unsigned integer with the given number of bytes at *vmaddr*.'
        align = self.align
        cow = self._cowlayer
        if not length:
            length = align
        item = vmaddr >> self._rightShift
        if item in cow:
            obj = cow[item]
            if length == align:
                return obj
            elif length < align:
                return decompose(obj, vmaddr & (align-1), length)
            else:
                nextVal = self.get(vmaddr + align, length - align)
                return obj | nextVal << (align * 8)
        else:
            bs = self.ROM.derefBytes(vmaddr, length)
            return _strus[length].unpack(bs)[0]
            
    def set(self, vmaddr, value, length=0):
        'Set an unsigned integer with the given number of bytes at *vmaddr* to *value*.'
        align = self.align
        cow = self._cowlayer
        if not length:
            length = align
        item = vmaddr >> self._rightShift
        if item not in cow:
            lastItem = (vmaddr + length-1) >> self._rightShift
            sRdB = self.ROM.derefBytes
            sau = _strus[align].unpack
            for i in range(item, lastItem+1):
                bs = sRdB(i << self._rightShift, align)
                cow[i] = sau(bs)[0]
        if length == align:
            cow[item] = value
        elif length < align:
            cow[item] = replaceDecomposed(cow[item], vmaddr & (align-1), value, length)
        else:
            mask = (1 << (align*8)) - 1
            cow[item] = value & mask
            self.set(vmaddr + align, value >> (align*8), length - align)
            

class Stack(object):
    '''
    The class represents a stack.
    
    .. attribute:: align
    
        The native pointer width. 
    '''
    
    def __init__(self, align=4):
        self.content = deque()
        self.positiveLength = -1
        self.negativeLength = 0
        self.align = align
        self._rightShift = (align-1).bit_length()

    def __ensureItemExists(self, item):
        if item > self.positiveLength:
            self.content.extend(repeat(0, item + 1 - self.positiveLength))
            self.positiveLength = item + 1
        elif item < self.negativeLength:
            self.content.extendleft(repeat(0, self.negativeLength - item + 1))
            self.negativeLength = item - 1

    def get(self, offset, length=0):
        'Get an unsigned integer with the given number of bytes at *offset*.'
        align = self.align
        if not length:
            length = align
        item = offset >> self._rightShift
        self.__ensureItemExists(item)
        obj = self.content[item - self.negativeLength]
        if length == align:
            return obj
        elif length < align:
            return decompose(obj, offset & (align-1), length)
        else:
            nextVal = self.get(offset + align, length - align)
            return obj | (nextVal << (align * 8))
        
    def set(self, offset, value, length=0):
        'Set an unsigned integer with the given number of bytes at *offset* to *value*.'
        align = self.align
        if not length:
            length = align
        item = offset >> self._rightShift
        self.__ensureItemExists(item)
        index = item - self.negativeLength
        if length == align:
            self.content[index] = value
        elif length < align:
            self.content[index] = replaceDecomposed(self.content[item], offset & (align-1), value, length)
        else:
            mask = (1 << (align*8)) - 1
            self.content[index] = value & mask
            self.set(offset + align, value >> (align*8), length - align)

if __name__ == '__main__':
    assert decompose(0x12345678, 0, 1) == 0x78
    assert decompose(0x12345678, 1, 1) == 0x56
    assert decompose(0x12345678, 2, 1) == 0x34
    assert decompose(0x12345678, 3, 1) == 0x12
    assert decompose(0x12345678, 0, 2) == 0x5678
    assert decompose(0x12345678, 2, 2) == 0x1234

    assert replaceDecomposed(0x12345678, 0, 0xff, 1) == 0x123456ff
    assert replaceDecomposed(0x12345678, 1, 0xff, 1) == 0x1234ff78
    assert replaceDecomposed(0x12345678, 2, 0xff, 1) == 0x12ff5678
    assert replaceDecomposed(0x12345678, 3, 0xff, 1) == 0xff345678
    assert replaceDecomposed(0x12345678, 0, 0xff, 2) == 0x123400ff
    assert replaceDecomposed(0x12345678, 2, 0xff, 2) == 0x00ff5678
    
    romData = b'\x90\xef\xcd\xab\x78\x56\x34\x12'
    srom = SimulatedROM(romData, 0x1000)
    assert srom.vmaddr == 0x1000
    assert srom.content == romData
    assert srom.derefBytes(0x1002, 3) == b'\xcd\xab\x78'
    
    ram = RAM(srom)
    assert ram.get(0x1000) == 0xabcdef90
    assert ram.get(0x1004) == 0x12345678
    assert ram.get(0x1000, length=1) == 0x90
    assert ram.get(0x1001, length=1) == 0xef
    assert ram.get(0x1002, length=2) == 0xabcd
    assert ram.get(0x1000, length=8) == 0x12345678abcdef90
    
    ram.set(0x1001, 0x25, length=1)
    assert ram.get(0x1000) == 0xabcd2590
    assert ram.get(0x1004) == 0x12345678
    assert ram.get(0x1000, length=1) == 0x90
    assert ram.get(0x1001, length=1) == 0x25
    assert ram.get(0x1002, length=2) == 0xabcd
    assert ram.get(0x1000, length=8) == 0x12345678abcd2590
    
    ram.set(0x1004, 'test')
    assert ram.get(0x1000) == 0xabcd2590
    assert ram.get(0x1004) == 'test'
    
    ram.set(0x1002, 0x4321, length=2)
    assert ram.get(0x1000) == 0x43212590
    assert ram.get(0x1004) == 'test'
    assert ram.get(0x1002, length=1) == 0x21
    assert ram.get(0x1003, length=1) == 0x43
    assert ram.get(0x1000, length=2) == 0x2590
    
    ram.set(0x1000, 0x87654321abcdefff, length=8)
    assert ram.get(0x1000) == 0xabcdefff
    assert ram.get(0x1004) == 0x87654321
    assert ram.get(0x1000, length=8) == 0x87654321abcdefff
    
    stk = Stack()
    assert stk.get(0) == 0
    assert stk.get(0) == 0
    stk.set(0, 0x12345678)
    assert stk.get(0) == 0x12345678
    assert stk.get(2, length=2) == 0x1234
    stk.set(-4, 0xabcdef90)
    assert stk.get(-4) == 0xabcdef90
    assert stk.get(-4, length=8) == 0x12345678abcdef90
    stk.set(14, 0x4321, length=2)
    assert stk.get(14, length=2) == 0x4321
    assert stk.get(12) == 0x43210000
    stk.set(0, 0x1122334455667788, length=8)
    assert stk.get(0) == 0x55667788
    assert stk.get(4) == 0x11223344
    
