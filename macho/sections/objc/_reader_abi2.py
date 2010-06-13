#
#	_reader.py ... Read the Mach-O binary and parse into Objective-C stuff.
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

from objc.class_ import Class
from objc.method import Method
from objc.ivar import Ivar
from objc.property import Property
from objc.protocol import Protocol
from objc.category import Category
from macho.utilities import readStruct, peekStruct, peekStructs
import macho.loadcommands.segment	# to ensure macho.macho.MachO.[fromVM, derefString] are defined.

def _read_method(machO):
	#	typedef struct method_t {
	#		SEL name;
	#		const char *types;
	#		IMP imp;
	#	} method_t;
	(namePtr, encPtr, imp) = readStruct(machO.file, machO.makeStruct('3^'))
	name = machO.derefString(namePtr)
	encoding = machO.derefString(encPtr)
	return Method(name, encoding, imp)


def _read_ivar(machO):
	#	typedef struct ivar_t {
	#		// *offset is 64-bit by accident even though other 
	#		// fields restrict total instance size to 32-bit. 
	#		uintptr_t *offset;
	#		const char *name;
	#		const char *type;
	#		// alignment is sometimes -1; use ivar_alignment() instead
	#		uint32_t alignment  __attribute__((deprecated));
	#		uint32_t size;
	#	} ivar_t;
	(offsetPtr, namePtr, encPtr, _, _) = readStruct(machO.file, machO.makeStruct('3^2L'))
	offset = machO.deref(offsetPtr, '^')[0]
	name = machO.derefString(namePtr)
	encoding = machO.derefString(encPtr)
	return Ivar(name, encoding, offset)


def _read_prop(machO):
	#	struct objc_property {
	#		const char *name;
	#		const char *attributes;
	#	};
	(namePtr, attribPtr) = readStruct(machO.file, machO.makeStruct('2^'))
	name = machO.derefString(namePtr)
	attrib = machO.derefString(attribPtr)
	return Property(name, attrib)


# Just read any fixed-length structure.
def _read_list_at(machO, position, method):
	if position:
		machO.seek(machO.fromVM(position))
		(_, count) = readStruct(machO.file, machO.makeStruct('2L'))
		return list(reversed([method(machO) for i in range(count)]))
	else:
		return []


def readProtocols(protList, machO):
	"""Read a protocols pointed by the list of file offsets."""

	def _read_protocol_phase1(machO, loc):
		#	typedef struct protocol_t {
		#		id isa;
		#		const char *name;
		#		struct protocol_list_t *protocols;
		#		method_list_t *instanceMethods;
		#		method_list_t *classMethods;
		#		method_list_t *optionalInstanceMethods;
		#		method_list_t *optionalClassMethods;
		#		struct objc_property_list *instanceProperties;
		#	} protocol_t;
		
		machO.seek(loc)
		(_, namePtr, protocolList, instMethodsPtr, classMethodsPtr, optInstMethodsPtr, optClassMethodsPtr, propsPtr) = peekStruct(machO.file, machO.makeStruct('8^'))
		
		name = machO.derefString(namePtr)
		
		instMethods = _read_list_at(machO, instMethodsPtr, _read_method)
		classMethods = _read_list_at(machO, classMethodsPtr, _read_method)
		optInstMethods = _read_list_at(machO, optInstMethodsPtr, _read_method)
		optClassMethods = _read_list_at(machO, optClassMethodsPtr, _read_method)
		
		props = _read_list_at(machO, propsPtr, _read_prop)
		
		# we need to manage the protocol list after all protocols are read.
		proto = Protocol(name, instMethods, optInstMethods, classMethods, optClassMethods, props)
		return (proto, protocolList)
		
	def _read_protocol_phase2(machO, proto, protocolList, protoDict):
		#	typedef struct protocol_list_t {
		#		// count is 64-bit by accident. 
		#		uintptr_t count;
		#		protocol_ref_t list[0]; // variable-size
		#	} protocol_list_t;

		if protocolList:
			machO.seek(machO.fromVM(protocolList))
			ptrStru = machO.makeStruct('^')
			count = readStruct(machO.file, ptrStru)[0]
			protoAddrs = peekStructs(machO.file, ptrStru, count=count)
			proto.addProtocols(protoDict[i][0] for (i,) in protoAddrs)

	protos = {loc: _read_protocol_phase1(machO, loc) for loc in reversed(list(protList))}
	for proto, protocolList in protos.values():
		_read_protocol_phase2(machO, proto, protocolList, protos)
	
	return {k: v[0] for k, v in protos.items()}
	
def readClasses(classList, machO):
	def _read_class_ro_t(machO):
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
		
		(flags, instStart, instSize, _, name, methods, protos, ivars, _, props) = peekStruct(machO.file, machO.makeStruct('3L~7^'))
		


	def _read_class_t_phase1(machO, loc):
		#	typedef struct class_t {
		#		struct class_t *isa;
		#		struct class_t *superclass;
		#		Cache cache;
		#		IMP *vtable;
		#		class_rw_t *data;
		#	} class_t;
		
		# first, read the 
		machO.seek(machO.fromVM(loc))
		(isa, superclass, _, _, data) = peekStruct(machO.file, machO.makeStruct('5^'))
		machO.seek(machO.fromVM(isa))
		(_, _, _, _, metaData) = peekStruct(machO.file, machO.makeStruct('5^'))
		
		machO.seek(machO.fromVM(data))
		cls = _read_class_ro_t(machO)
		
	
	classes = {loc: for loc in reversed(list(classList))}
	
