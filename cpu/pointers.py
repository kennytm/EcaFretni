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


class SpecialPointer(object):
    '''The base class of all special pointers.
    
    .. attribute:: notmask
    
        Indicates the bit size of the pointer. It should be set to ``-1<<(N-1)``
        for an *N*-bit system.
    
    .. method:: __eq__(other)
        __ne__(other)
        __lt__(other)
        __gt__(other)
        __le__(other)
        __ge__(other)
        
        Compare two special pointers.
    
    .. method:: __and__(mask)
    
        The bitwise AND is special cased such that, if any of *mask*'s lowest 2
        bits are set, it will return ``self``; otherwise, it returns 0, e.g.
        
        >>> StackPointer(12) & ~0xfffffff
        0
        >>> StackPointer(12) & 0xffffffff
        StackPointer(12)

    .. method:: __rshift__(value)
    
        The right-shift operation is special cased such that it always returns
        0 when *value* is nonzero, e.g.
        
        >>> StackPointer(12) >> 31
        0
    
    .. method:: __lshift__(value)
    
        The left-shift operation is only defined when *value* is zero. In other
        cases, it returns ``NotImplemented``.
    
    .. method:: __add__(value)
    
        Move the pointer forward by *value* bytes.
    
    .. method:: __sub__(value)
    
        If *value* is an integer, move the stack pointer backward by *value*
        bytes. Otherwise, if *value* is a pointer of the same class, compute the
        distance between the two.
    '''
    
    def __and__(self, mask):
        return self if mask & 3 else 0
    
    def __rshift__(self, value):
        return 0 if value else self
    
    def __lshift__(self, value):
        return NotImplemented if value else self


def _signed(notmask, x):
    nm2 = 2 * notmask
    x &= ~nm2
    return x + nm2 if x & notmask else x


class __Return(SpecialPointer):
    def __lt__(self, other):
        return False if self is other else NotImplemented
    def __gt__(self, other):
        return False if self is other else NotImplemented
    def __le__(self, other):
        return True if self is other else NotImplemented
    def __ge__(self, other):
        return True if self is other else NotImplemented
    def __sub__(self, other):
        if self is other:
            return 0
        elif -1 <= other <= 1:
            return self
        else:
            return NotImplemented
    def __add__(self, other):
        return self if -1 <= other <= 1 else NotImplemented
    def __repr__(self):
        return 'Return'
Return = __Return()
'''A singleton object representing the return address. The function should stop
executing when jumping to this variable.'''




class StackPointer(SpecialPointer):
    '''
    This class represents a stack pointer in the memory.
    
    .. attribute:: offset
    
        The offset from the top of the stack.
    
    '''
    
    def __init__(self, offset=0, notmask=-1<<31):
        self.offset = offset
        self.notmask = notmask
        
    def __add__(self, value):
        return StackPointer( _signed(self.notmask, self.offset + value) )
        
    def __sub__(self, value):
        if isStackPointer(value):
            return _signed(self.notmask, self.offset - value.offset)
        else:    
            return StackPointer( _signed(self.notmask, self.offset - value) )
    
    def __eq__(self, other):
        return isStackPointer(other) and self.offset == other.offset
    def __ne__(self, other):
        return not (self == other)
    def __lt__(self, other):
        if isStackPointer(other):
            return self.offset < other.offset
        else:
            return NotImplemented
    def __gt__(self, other):
        if isStackPointer(other):
            return self.offset > other.offset
        else:
            return NotImplemented
    def __le__(self, other):
        if isStackPointer(other):
            return self.offset <= other.offset
        else:
            return NotImplemented
    def __ge__(self, other):
        if isStackPointer(other):
            return self.offset >= other.offset
        else:
            return NotImplemented
    def __repr__(self):
        return 'StackPointer({0})'.format(self.offset)



class HeapPointer(SpecialPointer):
    '''
    This class represents a pointer to a memory location on the heap. 
            
    .. attribute:: offset
    
        The offset from the pointer to the actual heap object.
    
    .. attribute:: handle
    
        The handle that identifies this heap pointer. Heap pointers having 
        different handles never overlap.
    
    '''
    
    def __init__(self, handle, offset=0, notmask=-1<<31):
        self.offset = offset
        self.handle = handle
        self.notmask = notmask
    
    def __add__(self, value):
        return HeapPointer(self.handle, _signed(self.notmask, self.offset + value) )
        
    def __sub__(self, value):
        if isHeapPointer(value):
            if self.handle == value.handle:
                return _signed(self.notmask, self.offset - value.offset)
            else:
                raise TypeError('Cannot compare two heap pointers having different handles.')
        else:    
            return HeapPointer(self.handle, _signed(self.notmask, self.offset - value) )

    def __eq__(self, other):
        return isHeapPointer(other) and self.handle == other.handle and self.offset == other.offset
    def __ne__(self, other):
        return not (self == other)
    def __lt__(self, other):
        if isHeapPointer(other) and self.handle == other.handle:
            return self.offset < other.offset
        else:
            return NotImplemented
    def __gt__(self, other):
        if isHeapPointer(other) and self.handle == other.handle:
            return self.offset > other.offset
        else:
            return NotImplemented
    def __le__(self, other):
        if isHeapPointer(other) and self.handle == other.handle:
            return self.offset <= other.offset
        else:
            return NotImplemented
    def __ge__(self, other):
        if isHeapPointer(other) and self.handle == other.handle:
            return self.offset >= other.offset
        else:
            return NotImplemented
    def __repr__(self):
        return 'HeapPointer({0}, offset={1})'.format(self.hande, self.offset)


def isStackPointer(obj):
    'Check if *obj* is a stack pointer.'
    return isinstance(obj, StackPointer)


def isHeapPointer(obj):
    'Check if *obj* is a heap pointer.'
    return isinstance(obj, HeapPointer)
