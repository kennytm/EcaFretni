#    
#    vmaddr.py ... Convert between VM address and file offset
#    Copyright (C) 2010  KennyTM~ <kennytm@gmail.com>
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

from .utilities import peekStruct, peekString
from .macho import MachO
from monkey_patching import patch

from operator import attrgetter
from collections import Hashable, Set


def _fromToVM(mappings, src, func):
    for mapping in mappings:
        res = func(mapping, src)
        if res >= 0:
            return res
    return -1


class Mapping(Hashable):
    '''This class represents a memory mapping.
    
    .. attribute:: address
    
        The VM address the segment will eventually map to.
    
    .. attribute:: size
    
        The total size of this mapping.
    
    .. attribute:: offset
    
        The offset in the file. It should be set to -1 if the mapping does not
        occupy file space (e.g. zero-filled sections). 
    
    .. attribute:: maxprot
    
        Maximum protection level.
        
    .. attribute:: initprot
    
        Initial protection level.
    '''
    
    def __init__(self, address, size, offset, maxprot, initprot):
        self.address = address
        self.size = size
        self.offset = max(-1, offset)
        self.maxprot = maxprot
        self.initprot = initprot
    
    def __repr__(self):
        return "Mapping(0x{0:x}, 0x{1:x}, 0x{2:x}, {3}, {4})".format(
            self.address, self.size, self.offset, self.maxprot, self.initprot)

    def copy(self):
        '''Create a copy of this mapping.'''
        return Mapping(self.address, self.size, self.offset, self.maxprot, self.initprot)

    __copy__ = copy

    def _toTuple(self):
        return (self.address, self.size, self.offset, self.maxprot, self.initprot)

    def __hash__(self):
        '''Compute the hash of this mapping.'''
        return hash(self._toTuple())
    
    def __eq__(self, other):
        '''Check if two mappings are equivalent.'''
        return self._toTuple() == other._toTuple()
    

    def fromVM(self, vmaddr):
        '''
        Convert a VM address to the corresponding offset in the file.
        
        Return -1 if the address is invalid.
        '''
        if self.offset >= 0 and self.address <= vmaddr < self.address + self.size:
            return vmaddr - self.address + self.offset
        else:
            return -1
        
    def toVM(self, offset):
        '''
        Convert a file offset to the corresponding VM address in the mapping.
        
        Return -1 if the offset is invalid.
        '''
        if 0 <= self.offset <= offset < self.offset + self.size:
            return offset - self.offset + self.address
        else:
            return -1
    

class MappingSet(Set):
    '''
    A container that stores :class:`Mapping`\s.     
    '''
    
    @property
    def mutable(self):
        'Check whether the mapping set is still mutable.'
        return isinstance(self._lst, set)
    
    def freeze(self):
        'Make mapping set immutable.'
        if self.mutable:
            self._lst = frozenset(self._lst)
        

    def fromVM(self, vmaddr):
        '''
        Convert a VM address to the corresponding offset in the file with this
        mapping set.
        
        Return -1 if the address is invalid.
        '''
        return _fromToVM(self._lst, vmaddr, Mapping.fromVM)
    
    
    def toVM(self, offset):
        '''
        Convert a file offset to the corresponding VM address with this mapping
        set.
        
        Return -1 if the offset is invalid.
        '''
        return _fromToVM(self._lst, offset, Mapping.toVM)
        
        
    def optimize(self):
        '''
        Optimize the mapping list by combining the consecutive ones.
        '''
        
        def _optimized():
            sortedMappings = iter(sorted(self._lst, key=attrgetter('address')))
            lastMapping = next(sortedMappings).copy()
            for mapping in sortedMappings:
                if lastMapping.offset >= 0 and \
                        mapping.address - lastMapping.address == lastMapping.size and \
                        mapping.offset - lastMapping.offset == lastMapping.size and \
                        mapping.initprot == lastMapping.initprot and \
                        mapping.maxprot == lastMapping.maxprot:
                    lastMapping.size += mapping.size
                else:
                    yield lastMapping
                    lastMapping = mapping.copy()
            yield lastMapping

        self._lst = set(_optimized())
        
        
    def __init__(self, lst=None):
        self._lst = set(lst or [])
        
    def __iter__(self):
        'Traverse of the mapping set.'
        return iter(self._lst)
    
    def __len__(self):
        'Get the length of mapping set.'
        return len(self._lst)
    
    def __contains__(self, mapping):
        'Check if *mapping* is in this mapping set.'
        return mapping in self._lst
    
    def add(self, mapping):
        '''
        Add a *mapping* to the mapping set.
        
        Raise an :exc:`AttributeError` if the set is already frozen.
        '''
        self._lst.add(mapping)
        
    def __repr__(self):
        return 'MappingSet({0!r})'.format(self._lst)


@patch
class MachO_VMAddr(MachO):
    '''
    This patch adds method to the :class:`~macho.macho.MachO` class for
    conversion between VM address and file offsets.
    
    .. attribute:: mappings
    
        The :class:`MappingSet` for this Mach-O file object.
        
    '''

    def fromVM(self, vmaddr):
        """Convert a VM address to file offset. Returns -1 if the address does
        not exist."""
        return self.mappings.fromVM(vmaddr)
    
    def toVM(self, offset):
        """Convert a file offset to VM address. Returns -1 if the address does
        not exist."""
        return self.mappings.toVM(offset)
    
    def deref(self, vmaddr, stru):
        '''Dereference a structure at VM address *vmaddr*. The structure is
        defined by the :class:`~struct.Struct` instance *stru*. Returns ``None``
        if the address does not exist.'''
        
        offset = self.mappings.fromVM(vmaddr)
        if offset < 0:
            return None
        return peekStruct(self.file, stru, position=offset + self.origin)

    def derefString(self, vmaddr, encoding='utf_8', returnLength=False):
        '''Read a null-terminated string at VM address *vmaddr*. Returns
        ``None`` if the address does not exist. See also
        :func:`macho.utilities.peekString` for meaning of other parameters.'''
        offset = self.fromVM(vmaddr)
        if offset < 0:
            return None
        return peekString(self.file, encoding=encoding, returnLength=returnLength, position=offset+self.origin)
        
    def derefBytes(self, vmaddr, length):
        '''Get bytes with length *length* at the VM address *vmaddr*. Returns
        a zero-filled :class:`bytes` if the address does not exist.'''
        offset = self.mappings.fromVM(vmaddr)
        if offset < 0:
            return bytes(length)
        return self.file[offset:offset+length]


if __name__ == '__main__':
    m1 = Mapping(address=1000, size=500, offset=1000, maxprot=7, initprot=7)
    m2 = Mapping(address=1500, size=1500, offset=1500, maxprot=7, initprot=7)    # m1 and m2 should be merged
    m3 = Mapping(address=3000, size=1000, offset=3000, maxprot=5, initprot=5)   # m2 and m3 should not be merged due to difference in protection level
    m4 = Mapping(address=4000, size=100, offset=5000, maxprot=5, initprot=5)    # m3 and m4 should not be merged as the file offsets are not consecutive
    m5 = Mapping(address=100000, size=500, offset=5100, maxprot=5, initprot=5)  # m4 and m5 should not be merged as the VM addresses are not consecutive
    m6 = Mapping(address=100500, size=15, offset=-1, maxprot=5, initprot=5)
    m7 = Mapping(address=100515, size=15, offset=14, maxprot=5, initprot=5) # m6 should not be merged to anywhere as the offset is -1
    
    mappings = MappingSet([m1, m3, m7, m6, m4])
    mappings.add(m5)
    assert m2 not in mappings
    mappings.add(m2)
    assert m2 in mappings
    assert len(mappings) == 7
    assert mappings.mutable
    assert mappings == MappingSet([m1, m2, m3, m4, m5, m6, m7])

    mappings.optimize()
    assert not mappings.mutable

    assert mappings == MappingSet([Mapping(address=1000, size=2000, offset=1000, maxprot=7, initprot=7), m3, m4, m5, m6, m7])
    
    assert mappings.fromVM(1750) == 1750
    assert mappings.fromVM(4009) == 5009
    assert mappings.fromVM(7302) == -1
    assert mappings.fromVM(100304) == 5404
    assert mappings.fromVM(100500) == -1
    assert mappings.fromVM(100515) == 14
    
    assert mappings.toVM(1750) == 1750
    assert mappings.toVM(4009) == -1
    assert mappings.toVM(5034) == 4034
    assert mappings.toVM(5134) == 100034
    assert mappings.toVM(0) == -1
    assert mappings.toVM(15) == 100516

