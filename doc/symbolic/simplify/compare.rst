:mod:`symbolic.simplify.compare` --- Simplification for comparison
==================================================================

Importing this module will perform simplification involving comparison
operators.

**Self comparison**

	When an expression is compared with itself, it can be reduced to a constant
	boolean value::
	
		(a == a) == True
	
**Negated comparison**

	Every comparison operator has a corresponding dual when the whole expression
	is negated::
	
		!(a < b) == (b <= a)
	
**Subtract and compare**

	Simple comparison like ``a < b`` is often executed as ``a - b < 0`` in the
	ALU. This rule reverts such transformation::
	
		(a - b < 0) == (a < b)
	
**Equality with zero**

	To check the truthness of an expression, it is often checked equality with
	zero. This rule converts this back to a boolean expression::
	
		(a == 0) == !a
