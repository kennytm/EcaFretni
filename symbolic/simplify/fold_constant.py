#	
#	fold_constant.py ... Simplification rule (Constant folding)
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

from symbolic.expression import Expression, Constant
from symbolic.simplify.utilities import performIf
from collections import Counter
import operator
import functools
import bits

__unaryFuncs = {
	'-': operator.neg,
	'~': operator.invert,
	'!': operator.not_
}
__binaryFuncs = {
	'/': operator.truediv,
	'//': operator.floordiv,
	'==': operator.eq,
	'!=': operator.ne,
	'>=': operator.ge,
	'<=': operator.le,
	'>': operator.gt,
	'<': operator.lt,
	'%': operator.mod,
	'**': operator.pow,
	'<<': bits.lshift,
	'>>': bits.rshift,
	'>>>': bits.urshift,
	'rol': bits.rol,
	'ror': bits.ror
}
__naryFuncs = {
	'+': (operator.add, 0),
	'*': (operator.mul, 1),
	'&': (operator.and_, -1),
	'|': (operator.or_, 0),
	'^': (operator.xor, 0)
}

def _unary(self):
	if self.type in __unaryFuncs and Expression.isConstant(self.children[0]):
		return Constant(__unaryFuncs[self.type](self.children[0].value))
	
def _binary(self):
	if self.type in __binaryFuncs and Expression.isConstant(self.children[0]) and Expression.isConstant(self.children[1]):
		return Constant(__binaryFuncs[self.type](self.children[0].value, self.children[1].value))

def _applyNtimes(oper, value, count, prev):
	# compute value `oper` value `oper` value `oper` ... with 'count' values.
	if oper == '+':
		return prev + value * count
	elif oper == '*':
		return prev * (value ** count)
	elif oper == '&':
		return prev & value
	elif oper == '|':
		return prev | value
	elif oper == '^':
		if count % 2 == 0:
			return prev
		else:
			return prev ^ value

__naryDefaultValue = {'+': 0, '*': 1, '&': -1, '|': 0, '^': 0, '&&': True, '||': False}

def _nary(self):
	if self.type in __naryDefaultValue:
		default = __naryDefaultValue[self.type]
		val = default
		rests = Counter()
		totalValCount = 0
		
		def _updateVal(child, count):
			nonlocal val, totalValCount
			if child.value != default:
				val = _applyNtimes(self.type, child.value, count, val)
			totalValCount += count
		
		(rests, _) = performIf(self.children, Expression.isConstant, _updateVal)
		
		if val != default:
			rests[Constant(val)] += 1
				
		if totalValCount > 1 or (totalValCount == 1 and val == default):
			return self.replaceChildren(rests)
			

__shortCircuitTarget = {'&&': False, '||': True, '&': 0, '|': -1, '*': 0}

def _shortCircuit(self):
	if self.type in __shortCircuitTarget:
		target = __shortCircuitTarget[self.type]
		targetType = type(target)
		
		for v in self.children:
			if Expression.isConstant(v):
				if targetType(v.value) == target:
					return Constant(target)

def _naryBaseCondition(self):
	if self.type in __naryDefaultValue:
		uniqueChildrenCount = len(self.children)
		if uniqueChildrenCount == 0:
			return Constant(__naryDefaultValue[self.type])
		elif uniqueChildrenCount == 1:
			(child, value) = list(self.children.items())[0]
			if value == 1:
				return child

def _evaluateIfThenElse(self):
	if self.type == '?:' and Expression.isConstant(self.children[0]):
		if self.children[0].value:
			return self.children[1]
		else:
			return self.children[2]
	else:
		return None

Expression.addSimplificationRule(_unary, 'fold constant (unary)')
Expression.addSimplificationRule(_binary, 'fold constant (binary)')
Expression.addSimplificationRule(_shortCircuit, 'short circuit')
Expression.addSimplificationRule(_nary, 'fold constant (N-ary)')
Expression.addSimplificationRule(_naryBaseCondition, 'base condition (N-ary)')
Expression.addSimplificationRule(_evaluateIfThenElse, 'constant condition (?:)')

if __name__ == '__main__':
	from symbolic.simplify.recursive import *
	from symbolic.expression import Symbol
	
	Expression.setDebugSimplify(True)

	a = Constant(3) / Constant(2)
	assert Constant(1.5) == a.simplify()
	
	a = Expression('+', Constant(1), Constant(5), Constant(12), Constant(44))
	assert Constant(62) == a.simplify()
	
	a = Expression.if_(Expression.ge(Constant(7), Constant(2)), Constant(11), Constant(55))
	assert Constant(11) == a.simplify()
	
	a = (Constant(1) ^ Constant(5) - Constant(122) // Constant(4)) ** Constant(2)
	assert Constant(676) == a.simplify()
	
	a = Expression('*', Symbol("foo"), Constant(0), Symbol("boo"))
	assert Constant(0) == a.simplify()
