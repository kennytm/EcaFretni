#
#	sorted_list.py ... Sorted list
#	Copyright (C) 2010  KennyTM~ <kennytm@gmail.com>
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from bisect import bisect_right

class SortedList(object):
	"""A list of items sorted by use count."""

	def __init__(self):
		self.items = []
		self.useCount = []
	
	def append(self, obj):
		"""Append an object with use count of 0."""
		self.items.append(obj)
		self.useCount.append(0)
	
	def __iter__(self):
		return iter(self.items)
	
	def use(self, obj, hint=0):
		"""Increase the use count of an object at the specific index by 1."""
		
		# Two cases where there's no need to change place.
		#  1. Already the most popular item.
		#  2. Even after increasing the use count, the next item is still more 
		#     popular.
		#
		# Note that we store the use count as negative numbers for compatibility
		# with bisect.
		#
		
		index = hint
		if self.items[index] != obj:
			# The hint isn't right! Find again.
			print(obj, index, self.items)
			index = self.items.index(obj)
		
		if index == 0 or self.useCount[index-1] < self.useCount[index]:
			self.useCount[index] -= 1
		
		else:
			# This case happens only when a[i-1] == a[i]
			target = self.useCount[index] - 1
			j = bisect_right(self.useCount, target, 0, index)
			
			# rotate everything in [j, index] to the right by 1 step.
			self.useCount[j+1:index+1] = self.useCount[j:index]
			self.useCount[j] = target
			
			self.items[j+1:index+1] = self.items[j:index]
			self.items[j] = obj
		
if __name__ == '__main__':
	p = SortedList()
	
	p.append('foo')
	p.append('bar')
	p.append('baz')
	assert p.items == ['foo', 'bar', 'baz']
	assert p.useCount == [0, 0, 0]
	
	p.use('foo')
	p.use('foo')
	assert p.items == ['foo', 'bar', 'baz']
	assert p.useCount == [-2, 0, 0]	
	
	p.use('bar')
	assert p.items == ['foo', 'bar', 'baz']
	assert p.useCount == [-2, -1, 0]
	
	p.use('bar')
	assert p.items == ['foo', 'bar', 'baz']
	assert p.useCount == [-2, -2, 0]
	
	p.use('bar')
	assert p.items == ['bar', 'foo', 'baz']
	assert p.useCount == [-3, -2, 0]
	
	p.use('baz')
	p.use('baz')
	assert p.items == ['bar', 'foo', 'baz']
	assert p.useCount == [-3, -2, -2]
	
	p.use('baz')
	assert p.items == ['bar', 'baz', 'foo']
	assert p.useCount == [-3, -3, -2]
	
	p.use('foo')
	assert p.items == ['bar', 'baz', 'foo']
	assert p.useCount == [-3, -3, -3]
	
	p.use('foo')
	assert p.items == ['foo', 'bar', 'baz']
	assert p.useCount == [-4, -3, -3]
	
	
			
