#	
#	symbol_ptr.py ... symbol pointer sections
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

from macho.sections.section import Section, S_NON_LAZY_SYMBOL_POINTERS, S_LAZY_SYMBOL_POINTERS, S_SYMBOL_STUBS, S_LAZY_DYLIB_SYMBOL_POINTERS

class SymbolPtrSection(Section):
	"""The symbol pointer sections (for example ``__DATA,__nl_symbol_ptr``) and
	symbol stub sections.
	
	Analyzing this section will resolve the indirect symbols."""
	
	
	def analyze(self, segment, machO):
		dysymtab = machO.loadCommands.any('className', 'DySymtabCommand')
		if dysymtab is None:			# Make sure the DYSYMTAB command exists.
			return False
		elif not dysymtab.isAnalyzed:	# and loaded
			return True
		elif not dysymtab.indirectsymoff:	# and has the indirect symbol table.
			return False
		
		symtab = machO.loadCommands.any('className', 'SymtabCommand')
		if symtab is None:
			return False
		elif not symtab.isAnalyzed:
			return True
		
		stride = self.reserved[1] or machO.pointerWidth
		count = self.size // stride
		symbols = machO.symbols
		symbols_append = symbols.append
		
		indirectSyms = dysymtab.indirectSymbols(self.reserved[0], self.size // stride, machO)
		symRemoveSet = set()
		symRemoveSet_add = symRemoveSet.add
		
		for i, addr in zip(indirectSyms, range(self.addr, self.addr + count*stride, stride)):
			syms = list(symbols.all('ordinal', i))
			# make a copy to break the reference when we call symbols.append
			for sym in list(syms):
				theSymbol = sym.copy()
				theSymbol.addr = addr
				if not sym.addr:
					symRemoveSet_add(sym)
				symbols_append(theSymbol, ordinal=i, addr=addr, name=theSymbol.name)
				
		symbols.removeMany(symRemoveSet)

		
		

Section.registerFactoryFType(S_NON_LAZY_SYMBOL_POINTERS, SymbolPtrSection.byFType)
# Section.registerFactoryFType(S_LAZY_SYMBOL_POINTERS, SymbolPtrSection.byFType)
# # - The __la_symbol_ptr adds nothing of value to the symbol table.
# Section.registerFactoryFType(S_LAZY_DYLIB_SYMBOL_POINTERS, SymbolPtrSection.byFType)
Section.registerFactoryFType(S_SYMBOL_STUBS, SymbolPtrSection.byFType)
