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
from cpu.pointers import isStackPointer, isHeapPointer, HeapPointer, StackPointer
from copy import deepcopy
from abc import ABCMeta, abstractmethod

_strus = (None, Struct('<B'), Struct('<H'), None, Struct('<I'), None, None, None, Struct('<Q'))
_best_length = (1, 1, 2, 4, 4, 8, 8, 8, 8)

class Memory(object):
    '''The complete memory model. This consists of a :class:`RAM`, a
    :class:`Stack` and a :class:`Heap`.
    
    .. attribute:: RAM
    
        The :class:`RAM` in this memory.
        
    .. attribute:: stack
    
        The :class:`Stack` in this memory.
        
    .. attribute:: heap
    
        The :class:`Heap` in this memory.
    
    '''
    
    def __init__(self, ROM, align=4):
        self.RAM = RAM(ROM, align)
        self.stack = Stack(align)
        self.heap = Heap()
        self.align = align
        
    def __copy__(self):
        'Create a completely isolated copy of this memory.'
        retval = type(self)(self.RAM.ROM, self.align)
        retval.RAM.copyFrom(self.RAM)
        retval.stack = deepcopy(self.stack)
        retval.heap = deepcopy(self.heap)
        return retval
        
        
    def get(self, pointer, length=0):
        'Get an integer at position indicated by *pointer*.'
        if not length:
            length = self.align
    
        if isStackPointer(pointer):
            return self.stack.get(pointer.offset, length)
        elif isHeapPointer(pointer):
            obj = self.heap.get(pointer.handle)
            if length < self.align or pointer.offset != 0:
                return decompose(obj, pointer.offset, length)
            else:
                return obj
        else:
            return self.RAM.get(pointer, length)
        
    def set(self, pointer, value, length=0):
        'Set an integer to the position indicated by *pointer*.'
        if not length:
            length = self.align

        if isStackPointer(pointer):
            self.stack.set(pointer.offset, value, length)
        elif isHeapPointer(pointer):
            if length < self.align or pointer.offset != 0:
                obj = self.heap.get(pointer.handle)
                value = replaceDecomposed(obj, pointer.offset, value, length)
            self.heap.set(pointer.handle, value)
        else:
            return self.RAM.set(pointer, value, length)
        
    def alloc(self, value):
        'Allocate heap space, and return the :class:`~cpu.pointers.HeapPointer`.'
        return HeapPointer(self.heap.alloc(value))
        
    def free(self, pointer):
        'Free the heap pointer.'
        self.heap.free(pointer.handle)
        

def decompose(obj, offset, length=-1):
    '''Decompose *obj* into bytes in little-endian, then return the value at
    *offset* with length *length*. For example,
    
    >>> decompose(0x12345678, 2, 1)
    0x34

    A negative length (the default) is equivalent to infinite length.
    
    >>> decompose(0x12345678, 2)
    0x1234

    This function is defined for integers only, but other classes could declare
    their ``decompose`` method to make this work too. The signature must be:: 
    
        def decompose(self, offset, length):
            ...
    
    and return an integer with *length* bytes.
    '''
    if isinstance(obj, int):
        rightShift = offset * 8
        if length >= 0:
            mask = ~(-1 << (length * 8))
            return (obj >> rightShift) & mask
        else:
            return obj >> rightShift
    else:
        return obj.decompose(offset, length)

def replaceDecomposed(obj, offset, value, length=-1):
    '''Decompose *obj* into bytes in little-endian, then replace the value at
    *offset* with length *length* by *value*. Return the new object containing
    the change as a result. For example,
    
    >>> replaceDecomposed(0x12345678, 2, 0xff, 1)
    0x12ff5678
    
    It is possible that *obj* be mutated when calling this function.
    
    A negative length (the default) is equivalent to infinite length.
    
    >>> replaceDecomposed(0x12345678, 2, 0xee)
    0xee5678
    
    This function is defined for integers only, but other classes could declare
    their ``replaceDecomposed`` method to make this work too. The signature must
    be:: 
    
        def replaceDecomposed(self, offset, value, length):
            ...
    '''
    if isinstance(obj, int):
        rightShift = offset * 8
        if length >= 0:
            mask = ~(-1 << (length * 8))
            obj &= ~(mask << rightShift)
        else:
            obj &= ~(-1 << rightShift)
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


# So, the general scheme of get/set functions are:
#
#   get(addr, length):
#       if addr is not aligned:
#           get the pre-excess part.
#           combine with get(addr+extraBytes, length-extraBytes)
#           return
#       else if length == align:
#           return getCore(item)
#       
class AlignedStorage(metaclass=ABCMeta):
    '''The abstract base class of all continuous mutable storages (:class:`RAM`
    and :class:`Stack`). The class defines the skeleton of how unaligned access
    should be performed.
    
    .. attribute:: align
    
        The native pointer width in bytes.
    '''
    
    def __init__(self, align=4):
        self.align = align
        self._rightShift = (align-1).bit_length()
    
    @abstractmethod
    def getItem(self, item, minLength):    # pragma: no cover
        '''Get an aligned item of the given index with at least *minLength*
        bytes. The value of item is related to the address by
        ``address == item * align``.
        
        This is an abstract method. All subclasses should override this method.
        '''
    
    @abstractmethod
    def setItem(self, item, value, minLength):    # pragma: no cover
        '''Set an aligned item by the given index with at least *minLength*
        bytes. The value of item is related to the address by
        ``address == item * align``.
        
        This is an abstract method. All subclasses should override this method.
        '''
    
    def get(self, offset, length=0):
        'Get an unsigned integer with the given number of bytes at *offset*.'
        align = self.align
        if not length:
            length = align
    
        item = offset >> self._rightShift
        unaligned = offset & (align-1)
        
        if unaligned:            
            bytesCount = min(align - unaligned, length)
            wholeObj = self.getItem(item, unaligned + bytesCount)
            alignedBytes = length - bytesCount
            obj = decompose(wholeObj, unaligned, bytesCount)
            if alignedBytes:
                higherObj = self.get(offset + bytesCount, alignedBytes)
                return replaceDecomposed(obj, bytesCount, higherObj)
            else:
                return obj
        
        elif length == align:
            return self.getItem(item, align)
        elif length < align:
            obj = self.getItem(item, length)
            return decompose(obj, 0, length)
        else:
            lowerObj = self.getItem(item, align)
            higherObj = self.get(offset + align, length - align)
            return replaceDecomposed(lowerObj, align, higherObj)

    def set(self, offset, value, length=0):
        'Set an unsigned integer with the given number of bytes at *offset* to *value*.'
        align = self.align
        if not length:
            length = align
    
        item = offset >> self._rightShift
        unaligned = offset & (align-1)

        if not unaligned:
            if length == align:
                self.setItem(item, value)
                return
            elif length > align:
                lowerObj = decompose(value, 0, align)
                higherObj = decompose(value, align)
                self.setItem(item, lowerObj)
                self.set(offset + align, higherObj, length - align)
                return
        
        bytesCount = min(align - unaligned, length)
        origObj = self.getItem(item, align)
        alignedBytes = length - bytesCount
        lowerObj = decompose(value, 0, bytesCount)
        newObj = replaceDecomposed(origObj, unaligned, lowerObj, bytesCount)
        self.setItem(item, newObj)
        if alignedBytes:
            higherObj = decompose(value, bytesCount)
            self.set(offset + bytesCount, higherObj, length - bytesCount)
            


class RAM(AlignedStorage):
    '''
    The class represents a RAM.
    
    .. attribute:: ROM
    
        The ROM it is operating on. This instance must be able to respond to the
        ``derefBytes`` function for dereferencing with signature::
        
            def derefBytes(self, vmaddr, length):
                ...
        
        where *vmaddr* is the VM address to dereference, and *length* is the
        number of bytes to get. It should return a buffer object.
    
    '''
    
    def __init__(self, ROM, align=4):
        assert hasattr(ROM, 'derefBytes')
        super().__init__(align)
        self._cowlayer = {}
        self.ROM = ROM
        
    def copyFrom(self, otherRAM):
        'Copy modified data from another RAM, which is backed by the same ROM.'
        if self.ROM is not otherRAM.ROM:
            raise ValueError('Cannot copy data from a RAM backed by another ROM.')
        self._cowlayer = deepcopy(otherRAM._cowlayer)
        
    def getItem(self, item, minLength):
        cow = self._cowlayer
        if item in cow:
            return cow[item]
        else:
            bestLength = _best_length[minLength]
            bs = self.ROM.derefBytes(item * self.align, bestLength)
            return _strus[bestLength].unpack(bs)[0]
            
    def setItem(self, item, value):
        self._cowlayer[item] = value
            

class Stack(AlignedStorage):
    '''
    The class represents a stack.
    
    .. attribute:: align
    
        The native pointer width. 
    '''
    
    def __init__(self, align=4):
        super().__init__(align)
        self.content = deque()
        self.positiveLength = -1
        self.negativeLength = 0
        
    def __ensureItemExists(self, item):
        if item > self.positiveLength:
            self.content.extend(repeat(0, item + 1 - self.positiveLength))
            self.positiveLength = item + 1
        elif item < self.negativeLength:
            self.content.extendleft(repeat(0, self.negativeLength - item + 1))
            self.negativeLength = item - 1

    def getItem(self, item, minLength):
        self.__ensureItemExists(item)
        return self.content[item - self.negativeLength]
    
    def setItem(self, item, value):
        self.__ensureItemExists(item)
        self.content[item - self.negativeLength] = value


class Heap(object):
    'This class represents a heap.'
    
    def __init__(self):
        self.content = {}
        self.nextHandle = 0
        
    def alloc(self, value=0):
        '''Allocate a new memory region on the heap, and assign it with value
        *value*. Return the handle of the allocated region.'''
        
        handle = self.nextHandle
        self.content[handle] = value
        self.nextHandle += 1
        return handle
    
    def free(self, handle):
        'Free the memory region with handle *handle* on the heap.'
        del self.content[handle]
    
    def get(self, handle):
        'Return the value associated with *handle*.'
        return self.content[handle]
    
    def set(self, handle, value):
        'Set the value associated with *handle*.'
        self.content[handle] = value


    
        

if __name__ == '__main__':
    assert decompose(0x12345678, 0, 1) == 0x78
    assert decompose(0x12345678, 1, 1) == 0x56
    assert decompose(0x12345678, 2, 1) == 0x34
    assert decompose(0x12345678, 3, 1) == 0x12
    assert decompose(0x12345678, 0, 2) == 0x5678
    assert decompose(0x12345678, 2, 2) == 0x1234
    assert decompose(0x12345678, 0) == 0x12345678
    assert decompose(0x12345678, 1) == 0x123456
    assert decompose(0x12345678, 2) == 0x1234

    assert replaceDecomposed(0x12345678, 0, 0xff, 1) == 0x123456ff
    assert replaceDecomposed(0x12345678, 1, 0xff, 1) == 0x1234ff78
    assert replaceDecomposed(0x12345678, 2, 0xff, 1) == 0x12ff5678
    assert replaceDecomposed(0x12345678, 3, 0xff, 1) == 0xff345678
    assert replaceDecomposed(0x12345678, 0, 0xff, 2) == 0x123400ff
    assert replaceDecomposed(0x12345678, 2, 0xff, 2) == 0x00ff5678
    assert replaceDecomposed(0x12345678, 0, 0xff) == 0xff
    assert replaceDecomposed(0x12345678, 1, 0xff) == 0xff78
    assert replaceDecomposed(0x12345678, 2, 0xff) == 0xff5678
    assert replaceDecomposed(0x12345678, 3, 0xff) == 0xff345678
    assert replaceDecomposed(0x12345678, 4, 0xffff) == 0xffff12345678
    assert replaceDecomposed(0x12345678, 5, 0xabc) == 0xabc0012345678
    
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
    
    heap = Heap()
    handle = heap.alloc('foo')
    assert heap.get(handle) == 'foo'
    heap.set(handle, 'bar')
    assert heap.get(handle) == 'bar'
    newhandle = heap.alloc(400)
    assert heap.get(newhandle) == 400
    assert heap.get(handle) == 'bar'
    heap.free(handle)
    assert heap.get(newhandle) == 400
    try:
        heap.get(handle)
    except KeyError:
        pass
    else:
        assert False
        
        
    mem = Memory(srom)
    assert mem.get(0x1000) == 0xabcdef90
    assert mem.get(StackPointer(0)) == 0
    heapPtr = mem.alloc(0x12345678)
    assert mem.get(heapPtr) == 0x12345678
    assert mem.get(heapPtr, length=1) == 0x78
    mem.set(heapPtr + 2, 0x6543, length=2)
    assert mem.get(heapPtr) == 0x65435678
    mem.set(0x1000, 'omg')
    assert mem.get(0x1000) == 'omg'
    mem.set(StackPointer(1), 0x13, length=1)
    assert mem.get(StackPointer(0)) == 0x1300
    mem.free(heapPtr)
    try:
        mem.get(heapPtr)
    except KeyError:
        pass
    else:
        assert False
    heapPtr = mem.alloc(0x1224)
    assert mem.get(heapPtr) == 0x1224

    mem2 = mem.__copy__()
    assert mem2.get(0x1000) == 'omg'
    assert mem2.get(StackPointer(0)) == 0x1300
    assert mem2.get(heapPtr) == 0x1224
    assert mem.get(0x1000) == 'omg'
    assert mem.get(StackPointer(0)) == 0x1300
    assert mem.get(heapPtr) == 0x1224
    mem.set(0x1000, heapPtr)
    assert mem2.get(0x1000) == 'omg'
    assert mem.get(0x1000) == heapPtr
    mem2.set(0x1000, 0x5566)
    assert mem2.get(0x1000) == 0x5566
    assert mem.get(0x1000) == heapPtr
    mem2.set(StackPointer(0), 0x4445)
    assert mem2.get(StackPointer(0)) == 0x4445
    assert mem.get(StackPointer(0)) == 0x1300
    mem.set(StackPointer(0), 'foobar')
    assert mem2.get(StackPointer(0)) == 0x4445
    assert mem.get(StackPointer(0)) == 'foobar'
    mem.set(heapPtr, 0)
    assert mem2.get(heapPtr) == 0x1224
    assert mem.get(heapPtr) == 0
    mem2.set(heapPtr, -442)
    assert mem2.get(heapPtr) == -442
    assert mem.get(heapPtr) == 0

    
