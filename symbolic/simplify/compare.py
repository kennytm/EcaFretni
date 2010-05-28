#	
#	compare.py ... Simplification involving comparison.
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

from symbolic.expression import Expression, Constant, Symbol
from symbolic.simplify.utilities import performIf
from collections import Counter

def _selfCompare(self):
	if self.type in ('==', '<='):
		if self.children[0] == self.children[1]:
			return Constant(True)
	elif self.type in ('!=', '<'):
		if self.children[0] == self.children[1]:
			return Constant(False)

def __findNonZeroSide(self):
	# Check if one side is zero.
	for i, c in enumerate(self.children):
		if Expression.isConstant(c) and c.value == 0:
			return (1 - i)
	return -1


def __isNegativeFactor(self):
	if self.type == '*':
		for c in self.children:
			if Expression.isConstant(c) and c.value < 0:
				return True
	return False


def _subtractionAndCompareWithZero(self):
	# a-b < 0    <=>    a < b
	if self.type in ('==', '<=', '!=', '<'):
		otherChildIndex = __findNonZeroSide(self)
		
		if otherChildIndex >= 0:
			otherChild = self.children[otherChildIndex]
			if otherChild.type == '+':
				negatedFactors = Counter()
				def addNegatedFactor(child, count):
					nonlocal negatedFactors
					negatedFactors[-child] += count
				
				(positiveFactors, anyNeg) = performIf(otherChild.children, __isNegativeFactor, addNegatedFactor)
				
				if anyNeg:
					lhs = otherChild.replaceChildren(positiveFactors)
					rhs = otherChild.replaceChildren(negatedFactors)
					return self.replaceChildren([lhs, rhs])


def _equalityWithZero(self):
	# a == 0     <=>    !a
	if self.type in ('==', '!='):
		otherChildIndex = __findNonZeroSide(self)
		
		if otherChildIndex >= 0:
			rv = self.children[otherChildIndex]
			if self.type == '==':
				rv = Expression.not_(rv)
			return rv

__negatedComparisonMap = {
	'==': '!=',
	'!=': '==',
	'<': '<=',
	'<=': '<'}

def _negatedComparison(self):
	# !(a < b)    <=>    b <= a

	if self.type == '!':
		child = self.children[0]
		if child.type in __negatedComparisonMap:
			return Expression(__negatedComparisonMap[child.type], child.children[1], child.children[0])
			


Expression.addSimplificationRule(_selfCompare, 'self comparison (a==a <=> True)')
Expression.addSimplificationRule(_negatedComparison, 'negated comparison (!(a<b) <=> b<=a)')
Expression.addSimplificationRule(_subtractionAndCompareWithZero, 'subtract and compare (a-b<0 <=> a<b)')
Expression.addSimplificationRule(_equalityWithZero, 'equality with zero (a==0 <=> !a)')


if __name__ == '__main__':
	import symbolic.simplify.recursive
	import symbolic.simplify.fold_constant
	import symbolic.simplify.distributive
	from symbolic.expression import Symbol

	Expression.setDebugSimplify(True)
	
	a = Expression.lt(Symbol('aaa'), Symbol('aaa'))
	assert Constant(False) == a.simplify()
	
	a = Expression.le(Symbol('aaa'), Symbol('aaa'))
	assert Constant(True) == a.simplify()
	
	a = Expression.eq(Constant(0), Symbol('aaa') - Symbol('bbb'))
	assert Expression.eq(Symbol('aaa'), Symbol('bbb')) == a.simplify()
	
	a = Expression.eq(Constant(0), Symbol('aaa') + Symbol('bbb'))
	assert Expression.not_(Symbol('aaa') + Symbol('bbb')) == a.simplify()
	
	a = Expression.not_(Expression.ge(Symbol('aaa'), Symbol('bbb')))
	assert Expression.lt(Symbol('aaa'), Symbol('bbb')) == a.simplify()
	

