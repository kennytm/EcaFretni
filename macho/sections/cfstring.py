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
import macho.loadcommands.segment	# to ensure macho.macho.fromVM is defined.

class CFStringSection(Section):
	"""A section of Core Foundation CFStrings."""
	
	def analyze(self, segment, machO):
		strings = {}
		addressesAndLengths = self.readStructs('4^', machO)
		
		for addr, (_, _, strAddr, strLen) in addressesAndLengths:
			machO.seek(machO.fromVM(strAddr))
			string = machO.readFixedLengthString(strLen)
			strings[addr] = string
			
		self._strings = strings

	
	def stringAt(self, address):
		"""Returns a string at specified vm address. Returns None if not found."""
		return self._strings.get(address, None)

Section.registerFactory('__cfstring', CFStringSection)

