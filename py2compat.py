#	
#	py2compat.py ... Compatibility package for Python 2.x
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

'''
This module defines classes that does not exist in previous versions of Python.
This allows interpreters based on legacy version of Python (e.g. Sphinx) not to
complain.
'''

try:
	from collections import Counter, OrderedDict
except ImportError:
	class Counter(object):
		pass
	class OrderedDict(object):
		pass

if not hasattr(Counter, 'subtract'):
	# Directly copied from http://svn.python.org/projects/python/trunk/Lib/collections.py (@r81515)
	#
	def _Counter_subtract(self, iterable=None, **kwds):
		'''Like dict.update() but subtracts counts instead of replacing them.
		Counts can be reduced below zero.  Both the inputs and outputs are
		allowed to contain zero and negative counts.

		Source can be an iterable, a dictionary, or another Counter instance.

		>>> c = Counter('which')
		>>> c.subtract('witch')           # subtract elements from another iterable
		>>> c.subtract(Counter('watch'))  # subtract elements from another counter
		>>> c['h']                        # 2 in which, minus 1 in witch, minus 1 in watch
		0
		>>> c['w']                        # 1 in which, minus 1 in witch, minus 1 in watch
		-1

		'''
		if iterable is not None:
			self_get = self.get
			if isinstance(iterable, Mapping):
				for elem, count in iterable.items():
					self[elem] = self_get(elem, 0) - count
			else:
				for elem in iterable:
					self[elem] = self_get(elem, 0) - 1
		if kwds:
			self.subtract(kwds)
		
	Counter.subtract = _Counter_subtract
