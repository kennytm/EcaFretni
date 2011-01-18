#	
#	dyld_info.py ... LC_DYLD_INFO[_ONLY] load command.
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

from .loadcommand import LoadCommand, LC_DYLD_INFO
from macho.symbol import Symbol, SYMTYPE_UNDEFINED, SYMTYPE_GENERIC
from macho.utilities import peekStruct, readULeb128, readSLeb128, readString
import macho.loadcommands.segment

def _bind(machO, size, symbols):
	libord = 0
	sym = None
	addr = 0
	
	f = machO.file
	
	end = f.tell() + size
		
	lcs_all = machO.loadCommands.all
	ptrwidth = machO.pointerWidth
	
	allSegs = lcs_all('className', 'SegmentCommand')
	
	while f.tell() < end:
		c = f.read_byte()
		imm = c & 0xf     # BIND_IMMEDIATE_MASK
		opcode = c & 0xf0 # BIND_OPCODE_MASK
		
		if opcode == 0:	# BIND_OPCODE_DONE
			pass
			
		elif opcode == 0x10:	# BIND_OPCODE_SET_DYLIB_ORDINAL_IMM
			libord = imm
			
		elif opcode == 0x20:	# BIND_OPCODE_SET_DYLIB_ORDINAL_ULEB
			libord = readULeb128(f)
			
		elif opcode == 0x30:	# BIND_OPCODE_SET_DYLIB_SPECIAL_IMM
			libord = (imm | 0xf0) if imm else 0
			
		elif opcode == 0x40:	# BIND_OPCODE_SET_SYMBOL_TRAILING_FLAGS_IMM
			sym = readString(f)
			
		elif opcode == 0x50:	# BIND_OPCODE_SET_TYPE_IMM
			pass
			
		elif opcode == 0x60:	# BIND_OPCODE_SET_ADDEND_SLEB
			readSLeb128(f)
			
		elif opcode == 0x70:	# BIND_OPCODE_SET_SEGMENT_AND_OFFSET_ULEB
			addr = allSegs[imm].vmaddr + readULeb128(f)
			
		elif opcode == 0x80:	# BIND_OPCODE_ADD_ADDR_ULEB
			addr += readULeb128(f)
			
		elif opcode == 0x90:	# BIND_OPCODE_DO_BIND
			symbols.append(Symbol(sym, addr, SYMTYPE_UNDEFINED, libord=libord))
			addr += ptrwidth
			
		elif opcode == 0xa0:	# BIND_OPCODE_DO_BIND_ADD_ADDR_ULEB
			symbols.append(Symbol(sym, addr, SYMTYPE_UNDEFINED, libord=libord))
			addr += ptrwidth + readULeb128(f)
			
		elif opcode == 0xb0:	# BIND_OPCODE_DO_BIND_ADD_ADDR_IMM_SCALED
			symbols.append(Symbol(sym, addr, SYMTYPE_UNDEFINED, libord=libord))
			addr += (imm+1) * ptrwidth
			
		elif opcode == 0xc0:	# BIND_OPCODE_DO_BIND_ULEB_TIMES_SKIPPING_ULEB
			count = readULeb128(f)
			skip = readULeb128(f)
			for i in range(count):
				symbols.append(Symbol(sym, addr, SYMTYPE_UNDEFINED, libord=libord))
				addr += skip + ptrwidth
	

def _recursiveProcessExportTrieNode(f, start, cur, end, prefix, symbols):
	if cur < end:
		f.seek(cur)
		termSize = f.read_byte()
		if termSize:
			sym = prefix
			readULeb128(f)
			addr = readULeb128(f)
			symbols.append(Symbol(sym, addr, SYMTYPE_GENERIC, extern=True))
		
		childCount = f.read_byte()
		for i in range(childCount):
			suffix = readString(f)
			offset = readULeb128(f)
			lastPos = f.tell()
			_recursiveProcessExportTrieNode(f, start, start + offset, end, prefix + suffix, symbols)
			f.seek(lastPos)


class DyldInfoCommand(LoadCommand):
	'''
	The dyld info (only) load command.
	
	This class performs decoding of the
	:const:`~macho.loadcommands.loadcommand.LC_DYLD_INFO` and
	``LC_DYLD_INFO_ONLY`` load commands. These two commands are introduced in
	Mac OS X 10.6 and iPhone OS 3.1 to supersede the
	:const:`~macho.loadcommands.loadcommand.LC_DYSYMTAB` command.
	These, known as *compressed dyld info* to Apple, includes a domain-specific
	assembly language to encode address binding, and a trie to store the export
	symbols.
	
	When analyzed, the symbols will be added back to the Mach-O object. See the
	:mod:`macho.symbol` module for how to access these symbols.
	'''

	def analyze(self, machO):
		(rebaseOff, rebaseSize, bindOff, bindSize, weakBindOff, weakBindSize, 
			lazyBindOff, lazyBindSize, exportOff, exportSize) = peekStruct(machO.file, machO.makeStruct('10L'))
		symbols = []
		
		if bindSize:
			machO.seek(bindOff)
			_bind(machO, bindSize, symbols)
		
		if weakBindSize:
			machO.seek(weakBindOff)
			_bind(machO, weakBindSize, symbols)
		
		if lazyBindSize:
			machO.seek(lazyBindOff)
			_bind(machO, lazyBindSize, symbols)
		
		if exportSize:
			exportOff += machO.origin
			_recursiveProcessExportTrieNode(machO.file, exportOff, exportOff, exportOff + exportSize, "", symbols)
		
		machO.addSymbols(symbols)


LoadCommand.registerFactory(LC_DYLD_INFO, DyldInfoCommand)

