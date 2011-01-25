#    
#    pointers.py ... Pointers
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

class __Return(object):
    def __str__(self):
        return 'return'
    def __repr__(self):
        return 'Return'
Return = __Return()
'''A singleton object representing the return address. The function should stop
executing when jumping to this variable.'''




class StackPointer(object):
    '''
    This class represents a stack pointer in the memory.
    
    .. attribute:: offset
    
        The offset from the top of the stack.
    
    '''
    
    def __init__(self, offset=0):
        self.offset = offset
        
    def __add__(self, value):
        'Move the stack pointer forward by *value* bytes.'
        return StackPointer(self.offset + value)
        
    def __sub__(self, value):
        '''
        If *value* is an integer, move the stack pointer backward by *value*
        bytes. Otherwise, if *value* is a :class:`StackPointer`, compute the
        distance between the two.
        '''
        if isStackPointer(value):
            return self.offset - value.offset
        else:    
            return StackPointer(self.offset - value)
    
    def __eq__(self, other):
        'Check if two stack pointers are equal.'
        return isStackPointer(other) and self.offset == other.offset
    def __ne__(self, other):
        'Check if two objects are not equal.'
        return not (self == other)
    def __lt__(self, other):
        'Check if a stack pointer is strictly before another.'
        if isStackPointer(other):
            return self.offset < other.offset
        else:
            return NotImplemented
    def __gt__(self, other):
        'Check if a stack pointer is strictly after another.'
        if isStackPointer(other):
            return self.offset > other.offset
        else:
            return NotImplemented
    def __le__(self, other):
        'Check if a stack pointer is before or equals to another.'
        if isStackPointer(other):
            return self.offset <= other.offset
        else:
            return NotImplemented
    def __ge__(self, other):
        'Check if a stack pointer is after or equals to another.'
        if isStackPointer(other):
            return self.offset >= other.offset
        else:
            return NotImplemented


def isStackPointer(obj):
    'Check if *obj* is a stack pointer.'
    return isinstance(obj, StackPointer)


class HeapPointer(object):
    '''
    This class represents a pointer to a memory location on the heap. 
            
    .. attribute:: offset
    
        The offset from the pointer to the actual heap object.
    
    .. attribute:: handle
    
        The handle that identifies this heap pointer. Heap pointers having 
        different handles never overlap.
    
    '''
    
    def __init__(self, handle, offset=0):
        self.offset = offset
        self.handle = handle
    
    def __add__(self, value):
        'Move the heap pointer forward by *value* bytes.'
        return HeapPointer(self.handle, self.offset + value)
        
    def __sub__(self, value):
        '''
        If *value* is an integer, move the heap pointer backward by *value*
        bytes. Otherwise, if *value* is a :class:`HeapPointer` with the same
        handle, compute the distance between the two.
        '''
        if isHeapPointer(value):
            if self.handle == value.handle:
                return self.offset - value.offset
            else:
                raise TypeError('Cannot compare two heap pointers having different handles.')
        else:    
            return HeapPointer(self.handle, self.offset - value)

    def __eq__(self, other):
        'Check if two heap pointers are equal.'
        return isHeapPointer(other) and self.handle == other.handle and self.offset == other.offset
    def __ne__(self, other):
        'Check if two objects are not equal.'
        return not (self == other)
    def __lt__(self, other):
        'Check if a heap pointer is strictly before another.'
        if isHeapPointer(other) and self.handle == other.handle:
            return self.offset < other.offset
        else:
            return NotImplemented
    def __gt__(self, other):
        'Check if a heap pointer is strictly after another.'
        if isHeapPointer(other) and self.handle == other.handle:
            return self.offset > other.offset
        else:
            return NotImplemented
    def __le__(self, other):
        'Check if a heap pointer is before or equals to another.'
        if isHeapPointer(other) and self.handle == other.handle:
            return self.offset <= other.offset
        else:
            return NotImplemented
    def __ge__(self, other):
        'Check if a heap pointer is after or equals to another.'
        if isHeapPointer(other) and self.handle == other.handle:
            return self.offset >= other.offset
        else:
            return NotImplemented
    

def isHeapPointer(obj):
    'Check if *obj* is a heap pointer.'
    return isinstance(obj, HeapPointer)
