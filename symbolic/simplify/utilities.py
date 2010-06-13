#	
#	utitlities.py ... Utilities for simplification.
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

from symbolic.py2compat import Counter

def performIf(counter, predicate, action):
	"""Filter the *counter* collection by a *predicate* and perform some
	*action* on them. Returns a tuple of whether anything satisfies the
	predicate, and the counter collection of unsatisfying items.
	
	The *predicate* should take a key of the counter collection, and returns a
	``bool``. The *action* should take a key and its count in the counter
	collection.
	
	Example:
	
	>>> pred = (lambda key: key % 2 == 0)
	>>> action = (lambda key, count: print('Key =', key, ' Count =', count))
	>>> performIf(Counter([1,1,2,3,6,6,6,6]), pred, action)
	Key = 2  Count = 1
	Key = 6  Count = 4
	(Counter({1: 2, 3: 1}), True)
	>>> performIf(Counter([1,1,3]), pred, action)
	(Counter({1: 2, 3: 1}), False)
	>>> performIf(Counter([2,6,6,6,6]), pred, action)
	Key = 2  Count = 1
	Key = 6  Count = 4
	(Counter(), True)
	
	"""

	return performIf2(counter, (lambda k, c: predicate(k)), action)

def performIf2(counter, predicate, action):
	"""Similar to :func:`performIf`, but the *predicate* accepts the count as
	the second argument."""
	
	normal = Counter()
	anyTrue = False
	for child, count in counter.items():
		if predicate(child, count):
			anyTrue = True
			action(child, count)
		else:
			normal[child] += count
	return (normal, anyTrue)

def keysExcept(counter, predicate):
	"""Returns an iterator of keys of the *counter* collection that does not
	satisfy the predicate.
	
	>>> pred = (lambda key: key % 2 == 0)
	>>> list(keysExcept(Counter([1,1,2,3,6,6,6,6]), pred))
	[1, 3]
	"""
	return (k for k in counter.keys() if not predicate(k))
