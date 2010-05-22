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
from macho.utilities import readFormatStruct, peekString

class Symbol(object):
	"""A symbol in Mach-O file."""
	
	@staticmethod
	def _getLibraryOrdinal(desc):
		return (desc >> 8) & 0xff
	
	def __init__(self, stroff, machO):
		(idx, typ, sect, desc, value) = machO.readFormatStruct('LBBH^')

		self.string = machO.peekString(position=stroff+idx)
		self.value = value
		
		self.library = None
		if typ & 1:	# N_EXT
			self.library = machO.allLoadCommands('DylibCommand')[self._getLibraryOrdinal(desc)]
		
		if desc & 8:	# N_ARM_THUMB_DEF
			self.value &= ~1
	
	def __str__(self):
		return "<Symbol {!r}:0x{:x}>".format(self.string, self.value)
		

class SymtabCommand(LoadCommand):
	"""The symtab (symbol table) load command."""
	
	@property
	def symbols(self):
		"""Get an ordered list of symbols."""
		return self._symbols

	@property
	def values(self):
		"""Get a dictionary of symbols indiced by address."""
		return self._values
	
	@property
	def strings(self):
		"""Get a dictionary of symbols indiced by address."""
		return self._strings
	
	
	def analyze(self):
		(symoff, nsyms, stroff, _) = self._o.readFormatStruct('4L')
		
		self._o.seek(symoff)
		symbols = []
		for i in range(nsyms):
			sym = Symbol(stroff, self._o)
			symbols.append(sym)
		
		self._symbols = symbols
		
		self._values = {s.value:s for s in symbols}
		self._strings = {s.string:s for s in symbols}
	
LoadCommand.registerFactory('SYMTAB', SymtabCommand)
		