:mod:`symbolic.simplify.fold_constant` --- Simplification by evaluating constant expressions
============================================================================================

Importing this module will evaluate constant expressions. 

**Fold constant**

	Whenever an expression's children are all constants, it can be evaluated to
	give a simple constant, e.g.::
	
		7 + 6 == 13
		  ~ 4 == -5
		      ...

**Fold constant (N-ary)**

	Commutative semigroup operators are all N-ary, hence it may only be partly
	composed of constants. This rule will evaluate the constant part, and leave
	the non-constant part untouched:: 
	
		a + 3 + 4 == a + 7
	
**Base condition**

	Commutative semigroup operators having exactly 0 children are equivalent to
	their identity value, and those having exactly 1 child can be replaced by
	the child::
	
		+(a) == a
		 +() == 0

**Short circuit**

	Some operators, when having a special constant as a child, the whole 
	expression must have the same value as it::
	
		0 * x == 0
	
	This rule is applied to ``*``, ``&``, ``|``, ``&&`` and ``||``.

**Constant condition**

	If the condition of the ``?:`` (conditional) operator is a constant, the 
	expression of the opposite truthness can be ignored::
	
		(1 ? t : f) == t
		(0 ? t : f) == f