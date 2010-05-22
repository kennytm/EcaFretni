#	
#	symbol.py ... Represents a symbol in a Mach-O file.
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

from macho.macho import MachO


class Symbol(object):
	"""A symbol in Mach-O file."""
	
	def __init__(self, string, value, library):
		(self.string, self.value, self.library) = (string, value, library)
	
	
	def __str__(self):
		return "<Symbol {!r}:0x{:x}>".format(self.string, self.value)
		


def _macho_addSymbols(self, symbols, fromSymtab=False):
	"""Add a list of symbols into MachO."""
	
	if not hasattr(self, '_symbols'):
		self._symbols = []
		self._symvals = {}
		self._symstrs = {}
	
	if fromSymtab:
		self._symbols.extend(symbols)
	
	self._symvals.update((sym.value, sym) for sym in symbols)
	self._symstrs.update((sym.string, sym) for sym in symbols)

def _macho_symbols(self):
	"""Get the list of symbols with ordinals."""
	return self._symbols
	
def _macho_getSymbol(self, string=None, value=None):
	"""Get a symbol by string or value (address)."""
	if string is not None:
		return self._symstrs.get(string, None)
	else:
		return self._symvals.get(value, None)
	
MachO.addSymbols = _macho_addSymbols
MachO.symbols = property(_macho_symbols)
MachO.getSymbol = _macho_getSymbol
