:mod:`symbolic.simplify.distributive` --- Simplification by applying distribution law
=====================================================================================

Importing this module will insert simplification rules involving distribution
law. These rules are:

**Repetition**

	Multiple copies of itself can be rewritten using a higher-rank operator::
	
		a + a + a == 3 * a
	
	This rule is applied to (``+``, ``*``) and (``*``, ``**``).

**Distributive**

	Also known as *factorization*, if the same subexpression appear in different
	terms, it can be taken out, like::
	
		a*b + a*c == a*(b + c)
	
	This is useful when the uncommon subexpressions are constants. Using
	together with the rules in :mod:`symbolic.simplify.fold_constant`, one could
	assert::
	
		3*a + 4*a == (3 + 4)*a    # distributive
		          == 7*a          # fold constant (binary)
	
	This rule is applied to (``+``, ``*``), (``|``, ``&``), (``&``, ``|``),
	(``&&``, ``||``) and (``||``, ``&&``).
	
