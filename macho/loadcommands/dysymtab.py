#	
#	dysymtab.py ... LC_DYSYMTAB load command.
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

from macho.loadcommands.loadcommand import LoadCommand, LC_DYSYMTAB
from macho.macho import MachOError
from macho.symbol import Symbol
from macho.utilities import peekPrimitives, peekStruct, peekStructs
from struct import Struct

class DySymtabCommand(LoadCommand):
	"""
	The ``DYSYMTAB`` (dynamic symbol table) load command. When analyzed, the
	external symbols will be added back to the Mach-O object. See the
	:mod:`macho.symbol` module for how to access these symbols.
	"""
		
	def _exrelIter(self, machO, extreloff, count):		
		machO.seek(extreloff)
		reloc_res = peekStructs(machO.file, machO.makeStruct('LL'), count)
		isBigEndian = machO.endian == '>'
		
		symbols = machO.symbols
		symbols_all = symbols.all
		
		for r_address, r_extra in reloc_res:
			if r_address & 0x80000000:
				# it's a scattered_relocation_info 
				raise MachOError('Analyzing scattered_relocation_info not implemented yet.')
			else:
				if isBigEndian:
					r_symbolnum = r_extra >> 8
					r_extern = r_extra & 0x10
				else:
					r_symbolnum = r_extra & 0xFFFFFF
					r_extern = r_extra & 0x8000000
				
				if not r_extern:
					raise MachOError('Analyzing non-extern relocation not implemented yet.')
				
				yield (r_symbolnum, r_address)
				
		
		
	
	def analyze(self, machO):
		# Make sure the SYMTAB command is ready.
		if not all(lc.isAnalyzed for lc in machO.loadCommands.all('className', 'SymtabCommand')):
			return True
	
		(     ilocalsym,      nlocalsym,
		      iextdefsym,     nextdefsym,
		      iundefsym,      nundefsym,
		      tocoff,         ntoc,
		      modtaboff,      nmodtab,
		      extrefsymoff,   nextrefsyms,
		 self.indirectsymoff, nindirectsyms,
		      extreloff,      nextrel,
		      locreloff,      nlocrel) = peekStruct(machO.file, machO.makeStruct('18L'))
		
		if nextrel:
			machO.provideAddresses(self._exrelIter(machO, extreloff, nextrel))
	
	
	def indirectSymbols(self, start, count, machO):
		'''Get symbol indices from the indirect symbol table, given the *start*
		index and the *count* of indices to retrieve.'''
		
		cur = machO.tell()
		machO.seek(self.indirectsymoff + start * 4) 
		retval = peekPrimitives(machO.file, 'L', count, machO.endian, machO.is64bit)
		machO.seek(cur)
		return retval
		

LoadCommand.registerFactory(LC_DYSYMTAB, DySymtabCommand)




