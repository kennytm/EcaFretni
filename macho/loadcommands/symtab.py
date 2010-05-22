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

from macho.loadcommands.loadcommand import LoadCommand
from macho.symbol import Symbol

def _getLibraryOrdinal(desc):
	return (desc >> 8) & 0xff	


class SymtabCommand(LoadCommand):
	"""The symtab (symbol table) load command."""
		
	def analyze(self, machO):
		(symoff, nsyms, stroff, _) = machO.readFormatStruct('4L')
		
		# Get all nlist structs
		machO.seek(symoff)
		nlists = []
		for i in range(nsyms):
			nlists.append(machO.readFormatStruct('LBBH^'))
		
		# Now analyze the nlist structs
		symbols = []
		allDylibs = machO.allLoadCommands('DylibCommand')
		for (idx, typ, sect, desc, value) in nlists:
			string = machO.peekString(position=stroff+idx)
			library = None
			extern = bool(typ & 1)	# N_EXT
			if extern:
				library = allDylibs[_getLibraryOrdinal(desc)]
			if desc & 8:	# N_ARM_THUMB_DEF
				value &= ~1
			symbols.append(Symbol(string, value, library, extern))
		
		# add those symbols back into the Mach-O.
		machO.addSymbols(symbols, fromSymtab=True)

LoadCommand.registerFactory('SYMTAB', SymtabCommand)




