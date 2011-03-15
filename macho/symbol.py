#    
#    symbol.py ... Symbols
#    Copyright (C) 2010  KennyTM~ <kennytm@gmail.com>
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#    

from data_table import DataTable
from .macho import MachO
from monkey_patching import patch
from sym import *

@patch
class MachO_SymbolPatches(MachO):
    '''
    This patch adds method to the :class:`~macho.macho.MachO` class for symbol
    processing.
    
    .. attribute:: symbols
    
        Returns a :class:`~data_table.DataTable` of :class:`~sym.Symbol`\\s
        ordered by insertion order, with the following column names: ``'name'``,
        ``'addr'`` and ``'ordinal'``.
        
    '''

    def addSymbols(self, symbols):
        '''Add an iterable of :class:`~sym.Symbol`\\s to this Mach-O object.'''
    
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
        
    
