#	
#	cfstring.py ... __DATA,__cfstring section
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

from macho.sections.section import Section
from macho.utilities import peekFixedLengthString
from macho.symbol import Symbol, SYMTYPE_CFSTRING
import macho.loadcommands.segment	# to ensure macho.macho.fromVM is defined.

def _stringReader(machO, addressesAndLengths):
	origin = machO.origin
	machO_fromVM = machO.fromVM
	machO_file = machO.file
	for addr, (_, _, strAddr, strLen) in addressesAndLengths:
		fileoff = machO_fromVM(strAddr)
		string = peekFixedLengthString(machO_file, strLen, position=fileoff+origin)
		yield Symbol(string, addr, SYMTYPE_CFSTRING)
		

class CFStringSection(Section):
	"""The CoreFoundation string (``__DATA,__cfstring``) section."""
	
	def analyze(self, segment, machO):
		cfstrStruct = machO.makeStruct('4^')
		addressesAndLengths = self.asStructs(cfstrStruct, machO, includeAddresses=True)
		machO.addSymbols(_stringReader(machO, addressesAndLengths))


Section.registerFactory('__cfstring', CFStringSection)

