#
#	protolist.py ... __DATA,__objc_protolist section.
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

from macho.sections.section import Section
import macho.sections.objc._reader_abi2

class ObjCProtoListSection(Section):
	def _analyze1(self, machO):
		pass

	def _analyze2(self, machO):
		# In ABI 2.0, the __DATA,__objc_protolist contains a list of file offsets
		# in native width and endian. These offsets will point to a protocol_t
		# structure as described in objc-runtime-new.h.
		 
		ptrStruct = machO.makeStruct('^')
		addressMaps = self.peekStructs(ptrStruct, machO)
		addresses = (l for _, (l, ) in addressMaps)
		self.protocols = macho.sections.objc._reader_abi2.readProtocols(addresses, machO)

	def analyze(self, segment, machO):
		if self.sectname == '__protocol':
			return self._analyze1(machO)
		else:
			return self._analyze2(machO)


Section.registerFactory('__objc_protolist', ObjCProtoListSection)
