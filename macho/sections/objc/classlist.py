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

class ObjCClassListSection(Section):
	def _analyze1(self, machO):

	def _analyze2(self, machO):
		if not 
	
		classes = self.readStructs('5^', machO)
		
		for addr, (isa, superclass, _, _, data) 

	def analyze(self, segment, machO):
		if self.sectname == '__class':
			return self._analyze1(machO)
		else:
			return self._analyze2(machO)


Section.registerFactory('__objc_classlist', CStringSection)

# In 1.0 ABI (__OBJC,__class section),
#
#	struct old_class {
#		struct old_class *isa;
#		struct old_class *super_class;
#		const char *name;
#		long version;
#		long info;
#		long instance_size;
#		struct old_ivar_list *ivars;
#		struct old_method_list **methodLists;
#		Cache cache;
#		struct old_protocol_list *protocols;
#		// CLS_EXT only
#		const char *ivar_layout;
#		struct old_class_ext *ext;
#	};
#
# In 2.0 ABI (__DATA,__objc_classlist section),
#
#	typedef struct class_t {
#		struct class_t *isa;
#		struct class_t *superclass;
#		Cache cache;
#		IMP *vtable;
#		class_ro_t *data;
#	} class_t;
#
#	typedef struct class_ro_t {
#		uint32_t flags;
#		uint32_t instanceStart;
#		uint32_t instanceSize;
#	#ifdef __LP64__
#		uint32_t reserved;
#	#endif
#
#		const uint8_t * ivarLayout;
#		
#		const char * name;
#		const method_list_t * baseMethods;
#		const protocol_list_t * baseProtocols;
#		const ivar_list_t * ivars;
#
#		const uint8_t * weakIvarLayout;
#		const struct objc_property_list *baseProperties;
#	} class_ro_t;
#
