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

from collections import Counter

def performIf(counter, predicate, action):
	"""Filter the counter collection by a predicate and perform some action on
	them. Returns a tuple of whether anything satisfies the predicate, and the 
	counter collection of unsatisfying items.
	
	The "predicate" takes a key of the counter collection, and returns a boolean.
	
	The "action" takes a key and its count in the counter collection, and returns
	Nothing.
	
	"""

	return performIf2(counter, (lambda k, c: predicate(k)), action)

def performIf2(counter, predicate, action):
	"""Similar to performIf, but the predicate accepts the count argument as well."""
	
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
	"""Returns a generator of keys of the counter collection does not satisfy the
	predicate.
	
	"""
	return (k for k in counter.keys() if not predicate(k))
