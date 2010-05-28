#	
#	distributive.py ... Simplification using distributivity and existence of inverse.
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
from collections import Counter
from symbolic.simplify.utilities import performIf2, performIf, keysExcept

import symbolic.simplify.semigroup	# for the idempotent rule.

# The generalized distributive law for 3 operators +, #, * is that:
#
#    forall a,b,c.  a * b # a * c == a * (b+c)
#                   b * a # c * a == (b#c) * a
#
# Satisfying examples:
#
#      (+, #, *) -> (+, *, ^)
#
# This reduces to normal distributive law if (+) == (#), e.g.
#
#      (+, *)
#      (&, |)
#      (|, &)
#      (&&, ||)
#      (||, &&)

__distributions = {
	'+': '*',
	'|': '&',
	'&': '|',
	'||': '&&',
	'&&': '||'
}

def _repetition(self):
	# a + a + a = 3*a
	if self.type in ('+', '*'):
		star = '*' if self.type == '+' else '^'
		
		grouped = []
		def _evaluteRepetition(child, count):
			grouped.append(Expression(star, child, Constant(count)))
		
		(rest, hasRep) = performIf2(self.children, (lambda k, c: c != 1), _evaluteRepetition)
		
		if hasRep:
			rest.update(grouped)
			return self.replaceChildren(rest)
			

def _distributive(self):
	if self.type in __distributions:
		star = __distributions[self.type]
		
		extracted = []
		factorList = Counter()
		def _pushToExtracted(child, count):
			assert count == 1
			extracted.append(child)
			factorList.update(keysExcept(child.children, Expression.isConstant))
		
		(rest, hasStar) = performIf(self.children, Expression.isType(star), _pushToExtracted)
		
		if hasStar:
			# Algorithm for factorization:
			#
			#  1. find the most common factor
			#  2. check if that factor has appeared >1 times. If no, quit.
			#  3. otherwise, scan for all children which contain that factor.
			#  4. remove that factor from those children, and create a new
			#     a*(b+c+d) style expression.
			
			factorizedOnce = False
			while factorList:
				(commonest, count) = factorList.most_common(1)[0]
				if count == 1:
					if factorizedOnce:
						rest.update(extracted)
						return self.replaceChildren(rest)
					else:
						return None
				else:
					factorizedOnce = True
					oldExtracted = extracted
					extracted = []
					newChildrenList = []
					for child in oldExtracted:
						if commonest in child.children:
							factorList.subtract(keysExcept(child.children, Expression.isConstant))
							newChildChildren = Counter(child.children)
							newChildChildren[commonest] -= 1
							newChild = child.replaceChildren(newChildChildren)
							newChildrenList.append(newChild)
						else:
							extracted.append(child)
					newExpression = Expression(star, commonest, Expression(self.type, *newChildrenList))
					extracted.append(newExpression)
					factorList.update(keysExcept(child.children, Expression.isConstant))
							


Expression.addSimplificationRule(_repetition, 'repetition (a+a+a=3*a)')
Expression.addSimplificationRule(_distributive, 'distributive (a*b+a*c=a*(b+c))')

if __name__ == '__main__':
	import symbolic.simplify.recursive
	from symbolic.expression import Symbol

	Expression.setDebugSimplify(True)
	
	a = Expression('+', Symbol('a'), Symbol('a'), Symbol('b'), Symbol('a'), Symbol('b'), Symbol('b'), Symbol('a'), Symbol('c')) + \
		Expression('+', Symbol('c'), Symbol('a'), Symbol('c'), Symbol('c'), Symbol('b'), Symbol('a'), Symbol('a'), Symbol('d'))
	assert a.simplify() == Expression('+', Expression('*', Symbol('a'), Constant(7)),
	                                       Expression('*', Symbol('b'), Constant(4)),
                                          Expression('*', Symbol('c'), Constant(4)), Symbol('d'))
	

