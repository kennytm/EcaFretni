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
from macho.symbol import Symbol
from macho.utilities import peekPrimitives, peekStruct


class DySymtabCommand(LoadCommand):
	"""
	The ``DYSYMTAB`` (dynamic symbol table) load command. When analyzed, the
	external symbols will be added back to the Mach-O object. See the
	:mod:`macho.symbol` module for how to access these symbols.
	"""
		
	def _readExtrel(self, machO, count):
		pass
	
	def analyze(self, machO):
		(     ilocalsym,      nlocalsym,
		      iextdefsym,     nextdefsym,
		      iundefsym,      nundefsym,
		      tocoff,         ntoc,
		      modtaboff,      nmodtab,
		      extrefsymoff,   nextrefsyms,
		 self.indirectsymoff, nindirectsyms,
		      extreloff,      nextrel,
		      locreloff,      nlocrel) = peekStruct(machO.file, machO.makeStruct('18L'))
	
	
	def indirectSymbols(self, start, count, machO):
		'''Get symbol indices from the indirect symbol table, given the *start*
		index and the *count* of indices to retrieve.'''
		
		cur = machO.tell()
		machO.seek(self.indirectsymoff + start * 4) 
		retval = peekPrimitives(machO.file, 'L', count, machO.endian, machO.is64bit)
		machO.seek(cur)
		return retval
		

LoadCommand.registerFactory(LC_DYSYMTAB, DySymtabCommand)




