:mod:`macho.sections.section` --- Base class for all sections
=============================================================

.. automodule:: macho.sections.section
	:members:

Constants
---------

.. data:: S_REGULAR(0)
	S_ZEROFILL(1)
	S_CSTRING_LITERALS(2)
	S_4BYTE_LITERALS(3)
	S_8BYTE_LITERALS(4)
	S_LITERAL_POINTERS(5)
	S_NON_LAZY_SYMBOL_POINTERS(6)
	S_LAZY_SYMBOL_POINTERS(7)
	S_SYMBOL_STUBS(8)
	S_MOD_INIT_FUNC_POINTERS(9)
	S_MOD_TERM_FUNC_POINTERS(10)
	S_COALESCED(11)
	S_GB_ZEROFILL(12)
	S_INTERPOSING(13)
	S_16BYTE_LITERALS(14)
	S_DTRACE_DOF(15)
	S_LAZY_DYLIB_SYMBOL_POINTERS(16)
	S_THREAD_LOCAL_REGULAR(17)
	S_THREAD_LOCAL_ZEROFILL(18)
	S_THREAD_LOCAL_VARIABLES(19)
	S_THREAD_LOCAL_VARIABLE_POINTERS(20)
	S_THREAD_LOCAL_INIT_FUNCTION_POINTERS(21)

	The numerical value of each section type. See the `Mac OS X ABI Mach-O File
	Format Reference <http://developer.apple.com/mac/library/documentation/DeveloperTools/Conceptual/MachORuntime/Reference/reference.html#//apple_ref/doc/uid/20001298-section>`_
	for the definition of these.
