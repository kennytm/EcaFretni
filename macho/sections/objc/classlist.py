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
from ._abi1reader import analyzeClassList

class ObjCClassListSection(Section):
	"""The Objective-C class list section (``__DATA,__objc_classlist``, etc).
	
	.. attribute:: classes
	
		An :class:`~collections.OrderedDict` of :class:`~objc.class_.Class`\\es,
		keyed by their address.
	
	"""

	def _analyze1(self, machO, protoRefsMap):
		addressesAndClassTuples = self.asStructs(machO.makeStruct('12^'), machO, includeAddresses=True)
		self.classes = analyzeClassList(machO, addressesAndClassTuples, protoRefsMap)
		

	def _analyze2(self, machO, protoRefsMap):
		addresses = self.asPrimitives('^', machO)
		self.classes = readClassList(machO, addresses, protoRefsMap)
		

	def analyze(self, segment, machO):
		# Make sure the protocol sections is ready if exists.

		protoRefsMap = machO.anySectionProperty('className', 'ObjCProtoListSection', 'protocols', default={})
		if protoRefsMap is None:
			return True
	
		if self.segname == '__OBJC':
			self._analyze1(machO, protoRefsMap)
		else:
			self._analyze2(machO, protoRefsMap)


Section.registerFactory('__objc_classlist', ObjCClassListSection)	# __DATA,__objc_classlist
Section.registerFactory('__class_list', ObjCClassListSection)		# __OBJC2,__class_list
Section.registerFactory('__class', ObjCClassListSection)			# __OBJC,__class
# how about __DATA,__objc_nlclslist? what does it do?
