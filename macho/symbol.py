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

from data_table import DataTable
from .macho import MachO
from monkey_patching import patch

SYMTYPE_UNDEFINED = -1
SYMTYPE_GENERIC = 0
SYMTYPE_CSTRING = 3
SYMTYPE_CFSTRING = 4
SYMTYPE_OBJC_SEL = 5

_symtypeNames = dict((v, k) for k, v in globals().items() if k.startswith('SYMTYPE_'))

# This class should be moved away from the 'macho' package, since it is also
# meaningful for other executable file formats such as ELF and PE...
class Symbol(object):
	"""A symbol in Mach-O file.
	
	.. attribute:: name
	
		The name of the symbol.
	
	.. attribute:: addr
	
		The address of the symbol
	
	.. attribute:: ordinal
	
		Index of this symbol in the local symbol table. If it does not live in
		the symbol table, the ordinal is -1.
	
	.. attribute:: libord
	
		The "library ordinal" of this symbol. If this symbol is not undefined,
		this value should be 0.
		
		For Mach-O objects, the library can be recovered with the method
		:meth:`~macho.loadcommands.dylib.MachO_FromLibord.dylibFromLibord` 
		patched in :mod:`macho.loadcommands.dylib`.
		
	.. attribute:: extern
	
		A boolean indicating whether this is an exported symbol.
	
	.. attribute:: symtype
	
		The type of symbol. Can be one of:
		
		+----------------------------+-----------------------------------+
		| Value                      | Meaning                           |
		+============================+===================================+
		| ``SYMTYPE_UNDEFINED`` (-1) | Undefined (i.e. external) symbol. |
		+----------------------------+-----------------------------------+
		| ``SYMTYPE_GENERIC`` (0)    | Generic local symbol.             |
		+----------------------------+-----------------------------------+
		| ``SYMTYPE_CSTRING`` (3)    | C strings.                        |
		+----------------------------+-----------------------------------+
		| ``SYMTYPE_CFSTRING`` (4)   | CoreFoundation strings.           |
		+----------------------------+-----------------------------------+
		| ``SYMTYPE_OBJC_SEL`` (5)   | Objective-C selector.             |
		+----------------------------+-----------------------------------+
	
	"""
	
	def __init__(self, name, addr, symtype, ordinal=-1, libord=0, extern=False):
		self.name = name
		self.addr = addr
		self.symtype = symtype
		self.ordinal = ordinal
		self.libord = libord
		self.extern = extern
	
	def copy(self):
		'''Create a copy of this symbol.'''
		return type(self)(self.name, self.addr, self.symtype, self.ordinal, self.libord, self.extern)
	
	def _toTuple(self):
		return (self.name, self.addr, self.symtype, self.ordinal, self.libord, self.extern)

	def __eq__(self, other):
		return self._toTuple() == other._toTuple()
	
	def __hash__(self):
		return hash(self._toTuple())
		
	
	def __str__(self):
		return "<Symbol({}) '{}':0x{:x}>".format(_symtypeNames[self.symtype], self.name, self.addr)
		
	def __repr__(self):
		args = [repr(self.name), '0x{:x}'.format(self.addr), _symtypeNames[self.symtype]]
		if self.ordinal >= 0:
			args.append('ordinal={!r}'.format(self.ordinal))
		if self.libord:
			args.append('libord={!r}'.format(self.libord))
		if self.extern:
			args.append('extern=True')
		return 'Symbol({})'.format(', '.join(args))


@patch
class MachO_SymbolPatches(MachO):
	'''
	This patch adds method to the :class:`~macho.macho.MachO` class for symbol
	processing.
	
	.. attribute:: symbols
	
		Returns a :class:`~data_table.DataTable` of :class:`Symbol`\\s ordered
		by insertion order, with the following column names: ``'name'``,
		``'addr'`` and ``'ordinal'``.
		
	'''

	def addSymbols(self, symbols):
		'''Add an iterable of :class:`Symbol`\\s to this Mach-O object.'''
	
		if not hasattr(self, 'symbols'):
			self.symbols = DataTable('name', 'addr', '!ordinal')
		
		self_symbols_append = self.symbols.append
		for sym in symbols:
			self_symbols_append(sym, name=sym.name, addr=sym.addr, ordinal=sym.ordinal)
	
	def provideAddresses(self, ordinalsAndAddresses, columnName='ordinal'):
		'''Provide extra addresses to the symbols. The *ordinalsAndAddresses*
		parameter should be an iterable of (ordinal, address) tuple, e.g.::
		
			machO.provideAddresses([
			    (3000, 0x8e004),
			    (3001, 0x8e550),
			    (3002, 0x8e218),
			    ...
			])
		'''
		
		self_symbols = self.symbols
		self_symbols_any = self_symbols.any
		self_symbols_associate = self_symbols.associate
		
		for i, addr in ordinalsAndAddresses:
			theSymbol = self_symbols_any(columnName, i)
			if theSymbol:
				self_symbols_associate(theSymbol, 'addr', [addr])
		
	
