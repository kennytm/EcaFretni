:mod:`macho.loadcommands.loadcommand` --- Base class for all load commands
==========================================================================

.. automodule:: macho.loadcommands.loadcommand
	:members:

Constants 
---------

.. data:: LC_SEGMENT(0x01)
	LC_SYMTAB(0x02)
	LC_SYMSEG(0x03)
	LC_THREAD(0x04)
	LC_UNIXTHREAD(0x05)
	LC_LOADFVMLIB(0x06)
	LC_IDFVMLIB(0x07)
	LC_IDENT(0x08)
	LC_FVMFILE(0x09)
	LC_PREPAGE(0x0a)
	LC_DYSYMTAB(0x0b)
	LC_LOAD_DYLIB(0x0c)
	LC_ID_DYLIB(0x0d)
	LC_LOAD_DYLINKER(0x0e)
	LC_ID_DYLINKER(0x0f)
	LC_PREBOUND_DYLIB(0x10)
	LC_ROUTINES(0x11)
	LC_SUB_FRAMEWORK(0x12)
	LC_SUB_UMBRELLA(0x13)
	LC_SUB_CLIENT(0x14)
	LC_SUB_LIBRARY(0x15)
	LC_TWOLEVEL_HINTS(0x16)
	LC_PREBIND_CKSUM(0x17)
	LC_LOAD_WEAK_DYLIB(0x18)
	LC_SEGMENT_64(0x19)
	LC_ROUTINES_64(0x1a)
	LC_UUID(0x1b)
	LC_RPATH(0x1c)
	LC_CODE_SIGNATURE(0x1d)
	LC_SEGMENT_SPLIT_INFO(0x1e)
	LC_REEXPORT_DYLIB(0x1f)
	LC_LAZY_LOAD_DYLIB(0x20)
	LC_ENCRYPTION_INFO(0x21)
	LC_DYLD_INFO(0x22)
	LC_LOAD_UPWARD_DYLIB(0x23)

	The numerical value of each load command type, ignoring the ``LC_REQ_DYLD``
	bit. See the `Mac OS X ABI Mach-O File Format Reference
	<http://developer.apple.com/mac/library/documentation/DeveloperTools/Conceptual/MachORuntime/Reference/reference.html#//apple_ref/doc/uid/20001298-load_command>`_
	for the definition of these.
