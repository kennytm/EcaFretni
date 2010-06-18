#
#	classlist.py ... __DATA,__objc_classlist section.
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
from ._abi2reader import readClassList
from .protolist import ObjCProtoListSection

class ObjCClassListSection(Section):
	def _analyze1(self, machO):
		assert False, "Analyzing ABI 1.0 for the __OBJC,__class section is not implemented yet."

	def _analyze2(self, machO):
		# Make sure the protocol section is ready if exists.
		
		protoSect = machO.anySection(ObjCProtoListSection)
		if protoSect:
			if hasattr(protoSect, 'protocols'):
				protoRefsMap = protoSect.protocols
			else:
				return True
		else:
			protoRefsMap = {}
		
		addresses = self.asPrimitives('^', machO)
		self.classes = readClassList(machO, addresses, protoRefsMap)
		

	def analyze(self, segment, machO):
		if self.sectname == '__class':
			return self._analyze1(machO)
		else:
			return self._analyze2(machO)


Section.registerFactory('__objc_classlist', ObjCClassListSection)
