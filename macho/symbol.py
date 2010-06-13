#	
#	symbol.py ... Symbols
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

'''

This module defines the :class:`Symbol` class representing a symbol in the Mach-O
format. It also adds 3 methods to the :class:`macho.macho.MachO` class for
symbol processing.

Patches
-------

.. method:: macho.macho.MachO.addSymbols(symbols, fromSymtab=False)

	Add a list of :class:`Symbol`\\s to the Mach-O file.

.. attribute:: macho.macho.MachO.symbols

	Returns a list of :class:`Symbol`\\s sorted by insertion order.

.. method:: macho.macho.MachO.getSymbol(val)

	Returns a symbol which has address or name same being *val*.

Classes
-------

'''

from .macho import MachO


class Symbol(object):
	"""A symbol in Mach-O file.
	
	.. attribute:: string
	
		The name of the symbol.
	
	.. attribute:: value
	
		The address of the symbol
	
	.. attribute:: library
	
		The :class:`macho.loadcommands.dylib.DylibCommand` object associated with
		this symbol.
	
	.. attribute:: extern
	
		A boolean indicating whether this is an external symbol.
	
	
	"""
	
	def __init__(self, string, value, library=None, extern=False):
		(self.string, self.value, self.library, self.extern) = (string, value, library, extern)
	
	
	def __str__(self):
		return "<Symbol {!r}:0x{:x}>".format(self.string, self.value)
		
	def __repr__(self):
		args = [repr(self.string), '0x{:x}'.format(self.value)]
		if self.library is not None:
			args.append('library={!r}'.format(self.library))
		if self.extern:
			args.append('extern=True')
		return 'Symbol({})'.format(', '.join(args))


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
	
def _macho_getSymbol(self, val):
	"""Get a symbol by string or value (address)."""
	if isinstance(val, str):
		return self._symstrs.get(val, None)
	else:
		return self._symvals.get(val, None)
	
MachO.addSymbols = _macho_addSymbols
MachO.symbols = property(_macho_symbols)
MachO.getSymbol = _macho_getSymbol
