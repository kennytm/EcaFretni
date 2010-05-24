#	
#	expression.py ... Simple symbolic arithmetic
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
from sorted_list import SortedList
from copy import deepcopy

class Expression(object):
	@staticmethod
	def isConstant(x):
		"""Checks if x is a constant value."""
		return isinstance(x, (int, float, bool))

	@staticmethod
	def isType(typ):
		"""Returns a functor that checks if the input has the specified type."""
		def checker(x):
			return isinstance(x, Expression) and x.type == typ
		return checker

	__commutativeOpers = set(['+', '*', '&', '|', '^', '&&', '||', '==', '!='])

	def __init__(self, typ, *args):
		self.type = typ
		concretizer = Counter if typ in self.__commutativeOpers else list
		self.children = concretizer(map(deepcopy, args))
		
		# Available types:
		#   +: Add (n-ary, constant must be at the 0th position)
		#   *: Multiply (n-ary, constant must be at the 0th position)
		#   /: Divide (binary)
		#   %: Mod (binary)
		# neg: Negate (unary)
		#  >>: Right-shift (binary)
		# >>>: Unsigned right-shift (binary)
		#  <<: Left-shift (binary) (folded to y*2^x if RHS is constant.)
		# rol: Rotate left (binary)
		# ror: Rotate right (binary)
		#   &: And (n-ary)
		#   |: Or (n-ary)
		#   ^: Xor (n-ary)
		#   ~: Not (unary)
		#  ?:: If-then-else (ternary)
		#  &&: Logical-and (n-ary)
		#  ||: Logical-or (n-ary)
		#   !: Logical-not (unary)
		#  fn: function-application (1-arg + n-ary).
		#  **: power (binary)
		#  ==: equality (binary)
		#  !=: inequality (binary)
		# >=, >, <, <=: etc. (binary)
		# deref: dereference.
	
	def addChild(self, x):
		"""Adds the expression object x as the children of this expression."""
		self.children.append(x)
	
	def replaceChildren(self, newChildren):
		"""Returns a copy of itself, but with new children."""
		cp = Expression(self.type)
		cp.children = newChildren
		return cp
	
	def __eq__(self, other):
		if not isinstance(other, Expression):
			return False
		else:
			return self.type == other.type and self.children == other.children

	def __hash__(self):
		# Warning: only use when you guarantee the expression is immutable.
		iterToHash = self.children.items() if isinstance(self.children, Counter) else self.children
		return hash((self.type, tuple(iterToHash)))

	def __str__(self):
		if isinstance(self.children, Counter):
			return '(' + self.type.join(
				('[{}]{}'.format(count, v) if count != 1 else str(v))
				for v, count in self.children.items()) + ')'
		elif len(self.children) == 2:
			return '(' + self.type.join(map(str, self.children)) + ')'
		else:
			return '{}({})'.format(self.type, ', '.join(map(str, self.children)))

	def __repr__(self):
		elems = self.children.elements() if isinstance(self.children, Counter) else self.children
		return 'Expression({!r}, {})'.format(self.type, ', '.join(map(repr, elems)))

	__simplicationRules = SortedList()

	@classmethod
	def addSimplificationRule(cls, rule, name):
		"""Adds a new simplification rule.
		
		The simplification rule takes exactly 1 argument: the expression. It
		should return the simplified expression, or None if no simplication was
		done.
		
		If None is returned, the expression should not be modified.
		
		"""
		cls.__simplicationRules.append((rule, name))

	__debugSimplify = False
	@classmethod
	def setDebugSimplify(cls, newVal):
		"""Set whether to debug simplification."""
		cls.__debugSimplify = newVal

	
	@classmethod
	def simplificationRules(cls):
		"""Get an iterator of simplification rules and the use count"""
		useCounts = cls.__simplicationRules.useCount
		rules = cls.__simplicationRules.items
		return ((r[1], -u) for u, r in zip(useCounts, rules))
	
	def simplify(self, getSimplifyState=False):
		"""Simplify the expression.
		
		If the getSimplifyState parameter is set to True, the return value will
		be an (Expression, bool) tuple. The last element means whether
		simplification has taken place.
		
		"""
		retval = self
		hasSimplified = False
		
		# For simulating goto.
		def _retval():
			if getSimplifyState:
				return (retval, hasSimplified)
			else:
				return retval
		
		while True:
			for i, (f, name) in enumerate(self.__simplicationRules):
				r = f(retval)
				if r is not None:
					self.__simplicationRules.use((f, name), hint=i)
				
					hasSimplified = True
					if self.__debugSimplify:
						print (name, ":", r, "<-", retval)
					retval = r
					# we stop when we have simplified to something no longer an
					# expression (i.e. an atomic value.)
					if not isinstance(retval, Expression):
						return _retval()
					break
			else:
				return _retval()

	def __neg__(self): return Expression('-', self)
	def __invert__(self): return Expression('~', self)

	def __add__(self, other): return Expression('+', self, other)
	def __radd__(self, other): return Expression('+', other, self)
	def __sub__(self, other): return self + (-other)
	def __rsub__(self, other): return (-self) + other
	def __mul__(self, other): return Expression('*', self, other)
	def __rmul__(self, other): return Expression('*', other, self)
	def __floordiv__(self, other): return Expression('//', self, other)
	def __truediv__(self, other): return Expression('/', self, other)
	def __rfloordiv__(self, other): return Expression('//', other, self)
	def __rtruediv__(self, other): return Expression('/', other, self)
	def __mod__(self, other): return Expression('%', self, other)
	def __rmod__(self, other): return Expression('%', other, self)
	def __pow__(self, other): return Expression('**', self, other)
	def __rpow__(self, other): return Expression('**', other, self)
	def __lshift__(self, other): return Expression('<<', self, other)
	def __rlshift__(self, other): return Expression('<<', other, self)
	def __rshift__(self, other): return Expression('>>', self, other)
	def __rrshift__(self, other): return Expression('>>', other, self)
	def __and__(self, other): return Expression('&', self, other)
	def __rand__(self, other): return Expression('&', other, self)
	def __or__(self, other): return Expression('|', self, other)
	def __ror__(self, other): return Expression('|', other, self)
	def __xor__(self, other): return Expression('^', self, other)
	def __rxor__(self, other): return Expression('^', other, self)
	
	@staticmethod
	def and_(x, y): return Expression('&&', x, y)
	@staticmethod
	def or_(x, y): return Expression('||', x, y)
	@staticmethod
	def not_(x): return Expression('!', x)
	@staticmethod
	def rol(x, y): return Expression('rol', x, y)
	@staticmethod
	def ror(x, y): return Expression('ror', x, y)
	@staticmethod
	def fn(fptr, *args): return Expression('fn', fptr, *args)
	@staticmethod
	def if_(cond, true, false): return Expression('?:', cond, true, false)

	@staticmethod
	def eq(x, y): return Expression('==', x, y)
	@staticmethod
	def ne(x, y): return Expression('!=', x, y)
	@staticmethod
	def gt(x, y): return Expression('>', x, y)
	@staticmethod
	def lt(x, y): return Expression('<', x, y)
	@staticmethod
	def ge(x, y): return Expression('>=', x, y)
	@staticmethod
	def le(x, y): return Expression('<=', x, y)
	
	