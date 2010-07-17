#	
#	symtab.py ... LC_SYMTAB load command.
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

from macho.loadcommands.loadcommand import LoadCommand, LC_SYMTAB
from macho.symbol import Symbol, SYMTYPE_UNDEFINED, SYMTYPE_GENERIC
from macho.utilities import peekStruct, peekStructs, peekString


class SymtabCommand(LoadCommand):
	"""
	The :const:`~macho.loadcommands.loadcommand.LC_SYMTAB` load command. When
	analyzed, the symbols will be added back to the Mach-O object. See the
	:mod:`macho.symbol` module for how to access these symbols.
	"""
		
	def analyze(self, machO):
		symtabStruct = machO.makeStruct('4L')
		nlistStruct = machO.makeStruct('LBBH^')
		
		(symoff, nsyms, stroff, _) = peekStruct(machO.file, symtabStruct)
		
		# Get all nlist structs
		origin = machO.origin
		nlists = peekStructs(machO.file, nlistStruct, count=nsyms, position=symoff+origin)
		
		# Now analyze the nlist structs
		symbols = []
		for (ordinal, (idx, typ, sect, desc, value)) in enumerate(nlists):
			string = peekString(machO.file, position=stroff+idx+origin)
			libord = (desc >> 8) & 0xff  # GET_LIBRARY_ORDINAL
			extern = bool(typ & 1)       # N_EXT
			symtype = SYMTYPE_GENERIC if (typ & 0xe) else SYMTYPE_UNDEFINED
			if desc & 8:	# N_ARM_THUMB_DEF
				value &= ~1
			symbol = Symbol(string, value, symtype, ordinal, libord, extern)
			symbols.append(symbol)
		
		# add those symbols back into the Mach-O.
		machO.addSymbols(symbols)

LoadCommand.registerFactory(LC_SYMTAB, SymtabCommand)




