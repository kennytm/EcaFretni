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
from ._abi2reader import readCategoryList
from ._abi1reader import analyzeCategoryList

class ObjCCategoryListSection(Section):
	"""The Objective-C category list section (``__DATA,__objc_catlist``, etc).
	
	.. attribute:: categories
	
		A :class:`~data_table.DataTable` of :class:`~objc.category.Category`\\s,
		with the following columns:
		
		* ``'name'`` (string, the name of the category)
		
		* ``'base'`` (string, the name of the class the category is patching)
	
	"""

	def _analyze1(self, machO, classes, protoRefsMap):
		cats = self.asStructs(machO.makeStruct('5^L~^'), machO)
		# assert False, "Analyzing ABI 1.0 for the __OBJC,__category section is not implemented yet."
		self.categories = analyzeCategoryList(machO, cats, classes, protoRefsMap)

	def _analyze2(self, machO, classes, protoRefsMap):
		addresses = self.asPrimitives('^', machO)
		self.categories = readCategoryList(machO, addresses, classes, protoRefsMap)
		

	def analyze(self, segment, machO):
		# Make sure the classlist section is ready if exists.
		protoRefsMap = machO.anySectionProperty('className', 'ObjCProtoListSection', 'protocols', default={})
		classes = machO.anySectionProperty('className', 'ObjCClassListSection', 'classes', default={})
		
		if protoRefsMap is None or classes is None:
			return True
		if self.segname == '__OBJC':
			self._analyze1(machO, classes, protoRefsMap)
		else:
			self._analyze2(machO, classes, protoRefsMap)


Section.registerFactory('__objc_catlist', ObjCCategoryListSection)	# __DATA,__objc_catlist
Section.registerFactory('__category_list', ObjCCategoryListSection)	# __OBJC2,__category_list
Section.registerFactory('__category', ObjCCategoryListSection)	# __OBJC,__category (ABI 1.0)

