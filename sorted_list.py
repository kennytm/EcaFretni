#
#    sorted_list.py ... Sorted list
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

from bisect import bisect_right
from collections import Sequence, Sized

class SortedList(Sequence, Sized):
    """A simplistic sequence container, which is sorted automatically based on
    usage frequency::
    
        sl = SortedList()
        sl.append('foo')
        sl.append('bar')
        
        print (list(sl))
        # ['foo', 'bar']
        
        sl.use('bar')
        print (list(sl))
        # ['bar', 'foo']
    """

    def __init__(self):
        self._items = []
        self._useCount = []
    
    def append(self, obj):
        """Append an object with usage frequency of 0."""
        self._items.append(obj)
        self._useCount.append(0)
    
    def __getitem__(self, i):
        """
        Get the *i*-th object ranked by usage frequency. The 0th object will be
        the most frequently used one.
        """
        return self._items[i]
    
    def __len__(self):
        "Return the length of the list."
        return len(self._items)
    
    def use(self, obj, hint=0):
        '''
        Increase the usage frequency of *obj* by 1.
        
        If *hint* is given, it will be assumed the *obj* is at that rank. 
        '''
        # Two cases where there's no need to change place.
        #  1. Already the most popular item.
        #  2. Even after increasing the use count, the next item is still more 
        #     popular.
        #
        # Note that we store the use count as negative numbers for compatibility
        # with bisect.
        #
        
        self_items = self._items
        self_useCount = self._useCount
        
        index = hint
        if self_items[index] != obj:
            # The hint isn't right! Find again.
            index = self_items.index(obj)
        
        if index == 0 or self_useCount[index-1] < self_useCount[index]:
            self_useCount[index] -= 1
        
        else:
            # This case happens only when a[i-1] == a[i]
            target = self_useCount[index] - 1
            j = bisect_right(self_useCount, target, 0, index)
            
            # rotate everything in [j, index] to the right by 1 step.
            # e.g.         [a:-4, b:-3, c:-3, d:-3, e:-2]
            #     use d -> [a:-4, b:-3, c:-3, d:-4, e:-2]
            #    rotate -> [a:-4, d:-4, b:-3, c:-3, e:-2]
            #                     ^-- j       ^-- index
            self_useCount[j+1:index+1] = self_useCount[j:index]
            self_useCount[j] = target
            
            self_items[j+1:index+1] = self_items[j:index]
            self_items[j] = obj
        
        
        
if __name__ == '__main__':
    p = SortedList()
    
    p.append('foo')
    p.append('bar')
    p.append('baz')
    assert p._items == ['foo', 'bar', 'baz']
    assert p._useCount == [0, 0, 0]
    
    p.use('foo')
    p.use('foo')
    assert p._items == ['foo', 'bar', 'baz']
    assert p._useCount == [-2, 0, 0]    
    
    p.use('bar')
    assert p._items == ['foo', 'bar', 'baz']
    assert p._useCount == [-2, -1, 0]
    
    p.use('bar')
    assert p._items == ['foo', 'bar', 'baz']
    assert p._useCount == [-2, -2, 0]
    
    p.use('bar')
    assert p._items == ['bar', 'foo', 'baz']
    assert p._useCount == [-3, -2, 0]
    
    p.use('baz')
    p.use('baz')
    assert p._items == ['bar', 'foo', 'baz']
    assert p._useCount == [-3, -2, -2]
    
    p.use('baz')
    assert p._items == ['bar', 'baz', 'foo']
    assert p._useCount == [-3, -3, -2]
    
    p.use('foo')
    assert p._items == ['bar', 'baz', 'foo']
    assert p._useCount == [-3, -3, -3]
    
    p.use('foo')
    assert p._items == ['foo', 'bar', 'baz']
    assert p._useCount == [-4, -3, -3]
    
    assert p[0] == 'foo'
    assert len(p) == 3
    assert p.index('bar') == 1
    assert 'baz' in p
    assert list(p) == ['foo', 'bar', 'baz']
            
