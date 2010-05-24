#	
#	semigroup.py ... Perform simplification for the commutative semigroup operators.
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
from symbolic.simplify.utilities import split
from collections import Counter

# Commutative semigroup are mathematical structures for an operator + and set S,
# such that:
#
#   forall a,b,c.       (a + b) + c == a + (b + c)     (associative)
#   forall a,b.               a + b == b + a           (commutative)
#   exists 0. forall a.       0 + a == a
#
# A commutative monoid is called an abelian group if
#
#   forall a. exists -a.   a + (-a) == 0
#

def _flatten(self):
	# flatten an expression tree of the same type by applying associativity.
	# a + (b + c) == a + b + c.
	if self.type in ('+', '*', '&', '|', '^', '&&', '||'):
		rest = Counter()
		hasFlatten = False
		for child, count in self.children.items():
			if Expression.isType(self.type)(child):
				rest += child.children
				hasFlatten = True
			else:
				rest[child] += count
			
		if hasFlatten:
			return self.replaceChildren(rest)

def _idempotent(self):
	# (a & a) == a
	if self.type in ('&', '|', '&&', '||'):
		if any(count > 1 for count in self.children.values()):
			return Expression(self.type, *self.children.keys())

# 1-ary and 0-ary cases are handled in fold_constant.py already.

def _involution(self):
	# (a ^ a) == 0
	if self.type == '^':
		if any(count > 1 for count in self.children.values()):
			return Expression(self.type, *(k for k, c in self.children.items() if c % 2 != 0))

Expression.addSimplificationRule(_flatten, 'commutative semigroup (a*(b*c) == a*b*c)')
Expression.addSimplificationRule(_idempotent, 'idempotent ((a&a) == a)')
Expression.addSimplificationRule(_involution, 'involution ((a^a) == 0)')

if __name__ == '__main__':
	import symbolic.simplify.recursive

	Expression.setDebugSimplify(True)
	
	a = Expression('+', "foo", "bar") + "baz" + Expression('*', 'ma', 'maz') + Expression('-', 'y')
	assert a.simplify() == Expression('+', 'foo', 'bar', 'baz', Expression('*', 'ma', 'maz'), Expression('-', 'y'))
	
	a = (Expression('&', 'foo', 'bar', 'foo', 'baz', 'bar', 'bar') & Expression('^', 'foo', 'bar', 'foo', 'baz', 'bar', 'bar'))
	assert a.simplify() == Expression('&', 'foo', 'bar', 'baz', Expression('^', 'bar', 'baz'))
	


