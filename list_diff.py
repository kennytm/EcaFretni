#	
#	list_diff.py ... Compute lifetime of each element from snapshot of lists.
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

"""
This module provides a function :func:`versioning` to compute the diffs from
snapshots, and produce the lifetime of each element. Usage:

>>> import list_diff
>>> lists = [
...   [3, 1, 4, 1, 5, 9],
...   [3, 4, 1, 6, 9],
...   [1, 3, 4, 9, 9, 9],
...   [2, 2, 4, 5, 6, 8],
...   [2, 7, 2, 4, 5, 6, 8],
...   [2, 7, 1, 8, 2, 8]
... ]
>>> revs = list(list_diff.versioning(lists))
>>> for r in revs:
...     print("Element {0} exists from revisions {1} to {2}".format(r.content, r.low, r.high))
... 
Element 1 exists from revisions 2 to 2
Element 3 exists from revisions 0 to 2
Element 1 exists from revisions 0 to 0
Element 2 exists from revisions 3 to 5
Element 7 exists from revisions 4 to 5
Element 1 exists from revisions 5 to 5
Element 8 exists from revisions 5 to 5
Element 2 exists from revisions 3 to 5
Element 4 exists from revisions 0 to 4
Element 1 exists from revisions 0 to 1
Element 5 exists from revisions 0 to 0
Element 6 exists from revisions 1 to 1
Element 9 exists from revisions 0 to 2
Element 9 exists from revisions 2 to 2
Element 9 exists from revisions 2 to 2
Element 5 exists from revisions 3 to 4
Element 6 exists from revisions 3 to 4
Element 8 exists from revisions 3 to 5
>>> for i, l in enumerate(lists):
...     assert list(list_diff.snapshot(revs, i)) == l
... 
>>> 

"""

from itertools import chain
from difflib import SequenceMatcher



def _pairwise(lists):
	old = []
	for l in lists:
		yield (old, l)
		old = l

class Versioned(object):
	"""
	This class encapsulates an object and adds information about its
	(continuous) lifetime.
	
	.. data:: content
	
		The object
		
	.. data:: low
	
		The first version where the object starts to appear.
		
	.. data:: high
	
		The last version where the object still appears. 
	"""
	
	def __init__(self, content, low, high):
		self.content = content
		self.low = low
		self.high = high

	def __repr__(self):
		return "Versioned({0!r}, {1!r}, {2!r})".format(self.content, self.low, self.high)

def versioning(lists):
	"""
	Compute the lifetime of every element from an iterable of sequences. It 
	returns an iterable of :class:`Versioned` classes to indicate the lifetimes.
	
	The computation is backed by the built-in :mod:`difflib` module. As such,
	every element must be hashable. 
	"""
	
	ci = chain.from_iterable
	
	sm = SequenceMatcher()
	oldVersions = [ [] ]
	
	for newName, (oldList, newList) in enumerate(_pairwise(lists)):
		sm.set_seqs(oldList, newList)
		
		newVersions = [ oldVersions[0] ]

		for op, oldStart, oldEnd, newStart, newEnd in sm.get_opcodes():
			if op == 'equal':
				for i in range(oldStart+1, oldEnd+1):
					oldVersions[i][0].high = newName
				newVersions.extend(oldVersions[oldStart+1:oldEnd+1])

			if op == 'delete' or op == 'replace':
				newVersions[-1].extend(ci(oldVersions[oldStart+1:oldEnd+1]))
			
			if op == 'insert' or op == 'replace':
				newVersions.extend([Versioned(x, newName, newName)] for x in newList[newStart:newEnd])
		
		oldVersions = newVersions
	
	return ci(oldVersions)


def snapshot(versionedIterable, version):
	"""
	Recover an iterable at a particular version from an iterable of
	:class:`Versioned`\\s.
	"""
	return (v.content for v in versionedIterable if v.low <= version <= v.high)


if __name__ == '__main__':
	lists = [
	  [3, 1, 4, 1, 5, 9],
	  [3, 4, 1, 6, 9],
	  [1, 3, 4, 9, 9, 9],
	  [2, 2, 4, 5, 6, 8],
	  [2, 7, 2, 4, 5, 6, 8],
	  [2, 7, 1, 8, 2, 8]
	]
	revs = list(versioning(lists))
	for i, l in enumerate(lists):
		assert list(snapshot(revs, i)) == l
	
