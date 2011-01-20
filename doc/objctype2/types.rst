:mod:`objctype2.types` --- Types
================================

.. automodule:: objctype2.types
	:members:

Constants
---------

.. data:: BOOL('c')
	CHAR('c')
	SHORT('s')
	INT('i')
	LONG('l')
	LONG_LONG('q')
	UNSIGNED_CHAR('C')
	UNSIGNED_SHORT('S')
	UNSIGNED_INT('I')
	UNSIGNED_LONG('L')
	UNSIGNED_LONG_LONG('Q')
	FLOAT('f')
	DOUBLE('d')
	VOID('v')
	BOOL_C99('B')
	CLASS('#')
	SEL(':')
	FUNCTION_POINTER('^?')
	BLOCK('@?')
	NXATOM('%')
	
	Primitive type encodings.
	
.. data:: POINTER('^')
	COMPLEX('j')
	ONEWAY('V')
	CONST('r')
	BYCOPY('O')
	BYREF('R')
	IN('n')
	OUT('o')
	INOUT('N')
	GCINVISIBLE('!')
	
	Modifier type encodings.

