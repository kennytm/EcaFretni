#	
#	loadCommand.py ... Base class for all load commands
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

from factory import factory

@factory
class LoadCommand(object):
	"""An abstract load command."""
	
	def seek(self):
		"""Move the file pointer to the offset of this load command."""
		self._o.seek(self._offset)
	
	def analyze(self):
		"""Analyze the load command.
		
		The file pointer is guaranteed to be at the desired offset when this
		method is called from MachO.open().
		
		Return a true value to require further analysis."""
		
		return None
	
	def __init__(self, cmd, machO, size, offset):
		self._o = machO
		self._cmd = cmd
		self._size = size
		self._offset = offset

	@property
	def cmd(self):
		"""Get the name of this load command."""
		return self._cmd

	__names = [
		'SEGMENT',           # 0x1, segment of this file to be mapped
		'SYMTAB',            # 0x2, link-edit stab symbol table info
		'SYMSEG',            # 0x3, link-edit gdb symbol table info (obsolete)
		'THREAD',            # 0x4, thread
		'UNIXTHREAD',        # 0x5, unix thread (includes a stack)
		'LOADFVMLIB',        # 0x6, load a specified fixed VM shared library
		'IDFVMLIB',          # 0x7, fixed VM shared library identification
		'IDENT',             # 0x8, object identification info (obsolete)
		'FVMFILE',           # 0x9, fixed VM file inclusion (internal use)
		'PREPAGE',           # 0xa, prepage command (internal use)
		'DYSYMTAB',          # 0xb, dynamic link-edit symbol table info
		'LOAD_DYLIB',        # 0xc, load a dynamically linked shared library
		'ID_DYLIB',          # 0xd, dynamically linked shared lib ident
		'LOAD_DYLINKER',     # 0xe, load a dynamic linker
		'ID_DYLINKER',       # 0xf, dynamic linker identification
		'PREBOUND_DYLIB',    # 0x10, modules prebound for a dynamically
		
		'ROUTINES',          # 0x11, image routines
		'SUB_FRAMEWORK',     # 0x12, sub framework
		'SUB_UMBRELLA',      # 0x13, sub umbrella
		'SUB_CLIENT',        # 0x14, sub client
		'SUB_LIBRARY',       # 0x15, sub library
		'TWOLEVEL_HINTS',    # 0x16, two-level namespace lookup hints
		'PREBIND_CKSUM',     # 0x17, prebind checksum
		
		'LOAD_WEAK_DYLIB',   # 0x18, load a dynamically linked shared library that is allowed to be missing (all symbols are weak imported)
		
		'SEGMENT_64',        # 0x19, 64-bit segment of this file to be mapped
		'ROUTINES_64',       # 0x1a, 64-bit image routines
		'UUID',              # 0x1b, the uuid
		'RPATH',             # 0x1c, runpath additions
		'CODE_SIGNATURE',    # 0x1d, local of code signature
		'SEGMENT_SPLIT_INFO',# 0x1e, local of info to split segments
		'REEXPORT_DYLIB',    # 0x1f, load and re-export dylib
		'LAZY_LOAD_DYLIB',   # 0x20, delay load of dylib until first use
		'ENCRYPTION_INFO',   # 0x21, encrypted segment information
		'DYLD_INFO',         # 0x22, compressed dyld information
		'LOAD_UPWARD_DYLIB'  # 0x23, load upward dylib
	]
	__names_map = {j:i for i, j in enumerate(__names)}
		
	@classmethod
	def cmdname(cls, cmd):
		"""Get the name of the load command."""
		cmd &= ~0x80000000
		if 1 <= cmd <= len(cls.__names):
			return cls.__names[cmd-1]
		else:
			return None

	@classmethod
	def cmdindex(cls, name):
		return cls.__names_map.get(name, -1) + 1

	def __str__(self):
		return "<LoadCommand: LC_{}/{:x}>".format(self._cmd, self._offset)
