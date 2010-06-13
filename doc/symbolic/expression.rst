:tocdepth: 1

:mod:`symbolic.expression` --- Symbolic expressions
===================================================

.. automodule:: symbolic.expression
	:members:

Concepts
--------

A generic expression is represented by a tree. For example, the expression
``2 * (x + y/w + z/w)`` looks like::

	(*) -> 2
	       (+) -> x
	              (/) -> y
	                     w
	              (/) -> z
	                     w

There are 2 kinds of generic expressions:

* **Atomic** -- expressions which cannot be further simplified, which include:

  * **Constants** -- an atomic expression having a definite value that can be
    evaluated, e.g. ``89`` and ``-6.4``.
   
  * **Symbols** -- an unknown variable, e.g. ``x`` and ``y`` above.

* **Expression** -- any expressions that is not atomic, e.g. ``x + y`` and
  ``6 / 2``.



The :class:`Expression` class understands the following operators:

* **Commutative semigroup operators**. These operators are associative and
  commutative, thus form a `commutative semigroup
  <http://en.wikipedia.org/wiki/Semigroup>`_. These include:

  * ``+`` (addition)
  * ``*`` (multiplication)
  * ``&`` (bitwise AND)
  * ``|`` (bitwise OR)
  * ``^`` (bitwise XOR)
  * ``&&`` (logical AND)

  * ``||`` (logical OR)
  
  Their children are stored as a multiset (:class:`collections.Counter`).
 
* **Unary operators**. These contain exactly 1 child. These include:

  * ``~`` (bitwise NOT)

  * ``!`` (logical NOT)
	
  There is no negation operator. ``-x`` is represented by ``x * -1``. 

* **Binary operators**. These contain exactly 2 children, and their order
  cannot be swapped (i.e. non-commutative). These include:

  * ``//`` (integer division)
  * ``/`` (floating-point division)
  * ``%`` (modulus)
  * ``>>`` (right shift)
  * ``**`` (exponentiation)
  * ``rol`` (rotate left) and ``ror`` (rotate right)
  * ``==`` (equality) and ``!=`` (inequality)
  * ``<`` (less than) and ``<=`` (less than or equals to)

  The ``<<`` (left shift) operator should be written as ``x * 2**y``. The
  ``>`` (greater than) and ``>=`` (greater than or equals to) operators
  should be rewritten into ``<`` and ``<=`` with the arguments swapped.

* ``?:`` (conditional operator). This operator has exactly 3 children.

* ``fn`` (function application). This operator has at least 1 child, with
  the first child being the function to be applied on the rest of the
  children. The exact number of children depends on the arity of the
  function.
