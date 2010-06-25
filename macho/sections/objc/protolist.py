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
from ._abi2reader import readProtocolList
from ._abi1reader import analyzeProtocolList

class ObjCProtoListSection(Section):
	"""The Objective-C protocol list section (``__DATA,__objc_protolist``, etc).
	
	.. attribute:: protocols
	
		A :class:`~data_table.DataTable` of :class:`~objc.protocol.Protocol`\\s,
		with the following columns:
		
		* ``'name'`` (string, the name of the protocol)
		* ``'addr'`` (unique, integer, the VM address to the protocol)

	"""

	def _analyze1(self, machO):
		protos = self.asStructs(machO.makeStruct('5^'), machO, includeAddresses=True)
		self.protocols = analyzeProtocolList(machO, protos)

	def _analyze2(self, machO):
		# In ABI 2.0, the __DATA,__objc_protolist contains a list of file offsets
		# in native width and endian. These offsets will point to a protocol_t
		# structure as described in objc-runtime-new.h.
		addresses = self.asPrimitives('^', machO)
		self.protocols = readProtocolList(machO, addresses)

	def analyze(self, segment, machO):
		if self.segname == '__OBJC':
			return self._analyze1(machO)
		else:
			return self._analyze2(machO)


Section.registerFactory('__objc_protolist', ObjCProtoListSection)	# __DATA,__objc_protolist
Section.registerFactory('__protocol_list', ObjCProtoListSection)	# __OBJC2,__protocol_list
Section.registerFactory('__protocol', ObjCProtoListSection)			# __OBJC,__protocols (ABI 1.0)

