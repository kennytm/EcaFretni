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

'''
This module introduces the :class:`Expression` class, which is the basic element
of a symbolic expression.

Members
-------
'''

from py2compat import Counter
from sorted_list import SortedList
from copy import deepcopy

class Expression(object):
	'''
	The base class of all generic expressions. This is also the class
	representing an expression.
	
	There are two ways to construct an expression. You could rewrite the
	expression in prefix form, and use the initializer::
	
		# 2 * (x + y/w + z/w)
		Expression('*', Constant(2),
		                Expression('+', Symbol('x'),
		                                Expression('/', Symbol('y'), Symbol('w')),
		                                Expression('/', Symbol('z'), Symbol('w'))
		                )
		)
	
	However, this class also have overloaded several operators, that you could
	write it naturally::
	
		Constant(2) * (Symbol('x') + Symbol('y')/Symbol('w') + Symbol('x')/Symbol('w'))
	
	.. method:: __neg__(self)
		__invert__(self)
		__add__(self, other)
		__radd__(self, other)
		__sub__(self, other)
		__rsub__(self, other)
		__mul__(self, other)
		__rmul__(self, other)
		__floordiv__(self, other)
		__truediv__(self, other)
		__rfloordiv__(self, other)
		__rtruediv__(self, other)
		__mod__(self, other)
		__rmod__(self, other)
		__pow__(self, other)
		__rpow__(self, other)
		__lshift__(self, other)
		__rlshift__(self, other)
		__rshift__(self, other)
		__rrshift__(self, other)
		__and__(self, other)
		__rand__(self, other)
		__or__(self, other)
		__ror__(self, other)
		__xor__(self, other)
		__rxor__(self, other)
	
		These operators are overloaded for expression construction.

	.. staticmethod:: and_(x, y)
		or_(x, y)
		not_(x)
		rol(x, y)
		ror(x, y)
		fn(fptr, *args)
		if_(cond, true, false)
		eq(x, y)
		ne(x, y)
		gt(x, y)
		lt(x, y)
		ge(x, y)
		le(x, y)
		
		Convenient static methods to construct an expression.

	.. attribute:: children
	
		Children of this expression. It is a :class:`collections.Counter` if the
		type is a commutative semigroup operator, and a list if not.
	
	.. attribute:: type
	
		The operator type (e.g. ``'+'``, ``'*'``, etc.) of the expression.
	
	'''

	@staticmethod
	def isType(typ):
		'''
		Returns a functor that checks if the input has the specified type.
		Usage:
		
		>>> isPlus = Expression.isType('+')
		>>> isPlus(Expression('+', Constant(1), Constant(2)))
		True
		>>> isPlus(Expression('*', Constant(1), Constant(2)))
		False
		
		'''
		
		def checker(x):
			return x.type == typ
		return checker
		
	@staticmethod
	def isConstant(x):
		"""Checks whether the input is a :class:`Constant`."""
		return x.type == '<const>'

	@staticmethod
	def isAtomic(x):
		"""Checks whether the expression is atomic (i.e. cannot be further simplified)."""
		return x.type == '<const>' or x.type == '<symbol>'

	__associativeOpers = set(['+', '*', '&', '|', '^', '&&', '||'])

	def __init__(self, typ, *args):
		self.type = typ
		concretizer = Counter if typ in self.__associativeOpers else list
		self.children = concretizer(map(deepcopy, args))
		self._isConstant = False
		
		assert all(isinstance(k, type(self)) for k in self.children)
	
	def addChild(self, x):
		"""Append the expression *x* as the children of this expression."""
		self.children.append(x)
	
	def replaceChildren(self, newChildren):
		"""
		Returns a copy of itself, but replace the children with *newChildren*.
		Usage::
		
			>>> j = Expression('/', Constant(4), Constant(6))
			>>> j.replaceChildren([Constant(8), Constant(2)])
			Expression('/', Constant(8), Constant(2))
			>>> k = Expression('+', Constant(23), Constant(11))
			>>> k.replaceChildren(Counter([Constant(6), Constant(22), Symbol('x')]))
			Expression('+', Symbol('x'), Constant(22), Constant(6))
		
		"""
		cp = Expression(self.type)
		cp.children = newChildren
		return cp
	
	def __eq__(self, other):
		"""Compare equality of two expressions."""
		if not isinstance(other, type(self)):
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
		should return the simplified expression, or ``None`` if no simplication
		was done. If ``None`` is returned, the expression should not be modified.
		
		Usage::
		
			def powEval(expr):
			    if expr.type == '**':
			        if all(Expression.isConstant, expr.children):
			            return Constant(expr.children[0].value ** expr.children[1].value)
			
			Expression.addSimplificationRule(powEval, 'evaluate x ** y')
		
		"""
		cls.__simplicationRules.append((rule, name))

	__debugSimplify = False
	@classmethod
	def setDebugSimplify(cls, shouldDebug):
		"""Set whether to debug simplification."""
		cls.__debugSimplify = shouldDebug
	
#	@classmethod
#	def simplificationRules(cls):
#		"""Get an iterator of simplification rules and their use count"""
#		useCounts = cls.__simplicationRules.useCount
#		rules = cls.__simplicationRules.items
#		return ((r[1], -u) for u, r in zip(useCounts, rules))
	
	def simplify(self, getSimplifyState=False):
		"""Simplify the expression.
		
		.. note::
		
			By default there were no simplification routines available. Import
			modules from the subpackage :mod:`symbolic.simplify` to define them.
		
		If the *getSimplifyState* parameter is set to ``True``, the return value
		will be an (Expression, bool) tuple. The last element indicates whether
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

	def __neg__(self): return Expression('*', Constant(-1), self)
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
	def __lshift__(self, other): return Expression('*', self, Expression('**', Constant(2), other))
	def __rlshift__(self, other): return Expression('*', other, Expression('**', Constant(2), self))
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
	def gt(x, y): return Expression('<', y, x)
	@staticmethod
	def lt(x, y): return Expression('<', x, y)
	@staticmethod
	def ge(x, y): return Expression('<=', y, x)
	@staticmethod
	def le(x, y): return Expression('<=', x, y)

	
class Symbol(Expression):
	"""Creates a symbol. A :class:`Symbol` is an :class:`Expression` with
	:attr:`type` being ``'<symbol>'`` and have no children.
	
	.. attribute:: value
	
		Name of the symbol.
	
	"""
	def __init__(self, value):
		self.type = '<symbol>'
		self.value = value

	def __str__(self):
		return str(self.value)
	
	def __repr__(self):
		return '{}({!r})'.format(type(self).__name__, self.value)

	def __eq__(self, other):
		if not isinstance(other, type(self)):
			return False
		else:
			return self.value == other.value

	def __hash__(self):
		return hash((self.type, self.value))


class Constant(Symbol):
	"""Creates a constant. A :class:`Constant` is a :class:`Symbol` with
	:attr:`type` being ``'<const>'``.
	
	.. attribute:: value
	
		Value of the constant.
	
	"""
	def __init__(self, value):
		super().__init__(value)
		self.type = '<const>'
	

class Garbage(Symbol):
	pass
	
	
