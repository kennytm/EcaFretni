#	
#	recursive.py ... Recursively apply simplification to children.
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

from symbolic.expression import Expression
from collections import Counter

class _ChildSimplifier(object):
	def __init__(self):
		self.simplified = False
	
	def __call__(self, child):
		if not Expression.isAtomic(child):
			(child, hasSimplified) = child.simplify(getSimplifyState=True)
			self.simplified = self.simplified or hasSimplified
		return child


def _recursiveRule(self):
	if Expression.isAtomic(self):
		return None

	simplifier = _ChildSimplifier()
		
	if isinstance(self.children, Counter):
		retval = Counter({simplifier(child): count for child, count in self.children.items()})
	else:
		retval = [simplifier(child) for child in self.children]
						
	if simplifier.simplified:
		return self.replaceChildren(retval)
		
		
Expression.addSimplificationRule(_recursiveRule, 'recursive simplify')
