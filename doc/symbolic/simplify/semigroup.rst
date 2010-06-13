:mod:`symbolic.simplify.semigroup` --- Simplification involving one commutative semigroup operator
==================================================================================================

Importing this module will insert simplification rules involving one commutative
semigroup operator. These rules are:

**Commutative semigroup**

	Using commutativity and associativity, a hierachical tree can be flattened::
	
		a + (c + b) == a + b + c
	
	This rule is applied to all commutative semigroup operators (``+``, ``*``,
	``&``, ``|``, ``^``, ``&&``, ``||``).

**Idempotent**

	Some operators are *idempotent*, i.e.::
	
		(a & a) == a
	
	With this, extra copies of children can be reduced to one. This rule is
	applied to ``&``, ``|``, ``&&`` and ``||``.

**Involution**

	Some operators form *involution*, i.e.::
	
		(a ^ a) == 0
		           # identity element
		
	With this, extra copies of children can be reduced to one or zero. This rule
	is applied to ``^``.
	
