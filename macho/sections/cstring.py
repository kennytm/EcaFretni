#	
#	cstring.py ... __TEXT,__cstring section
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

from macho.sections.section import Section, S_CSTRING_LITERALS
from macho.utilities import readString
from macho.symbol import SYMTYPE_CSTRING, Symbol

def _stringReader(file, curAddr, final):
	while curAddr < final:
		(string, length) = readString(file, returnLength=True)
		if length:
			yield Symbol(string, curAddr, SYMTYPE_CSTRING)
		curAddr += length+1

class CStringSection(Section):
	"""The C string (``__TEXT,__cstring``) section."""
	
	def analyze(self, segment, machO):
		machO.addSymbols(_stringReader(machO.file, self.addr, self.addr + self.size))
	

Section.registerFactoryFType(S_CSTRING_LITERALS, CStringSection.byFType)


