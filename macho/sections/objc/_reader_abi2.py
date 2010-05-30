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

def _read_method(machO):
	#	typedef struct method_t {
	#		SEL name;
	#		const char *types;
	#		IMP imp;
	#	} method_t;
	(namePtr, encPtr, imp) = machO.readFormatStruct('3^')
	name = machO.peekString(position=machO.fromVM(namePtr))
	encoding = machO.peekString(position=machO.fromVM(encPtr))
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
	(offsetPtr, namePtr, encPtr, _, _) = machO.readFormatStruct('3^2L')
	offset = machO.deref(offsetPtr, '^')[0]
	name = machO.peekString(position=machO.fromVM(namePtr))
	encoding = machO.peekString(position=machO.fromVM(encPtr))
	return Ivar(name, encoding, offset)


def _read_prop(machO):
	#	struct objc_property {
	#		const char *name;
	#		const char *attributes;
	#	};
	(namePtr, attribPtr) = machO.readFormatStruct('2^')
	name = machO.peekString(position=machO.fromVM(namePtr))
	attrib = machO.peekString(position=machO.fromVM(attribPtr))
	return Property(name, attrib)


# Just read any fixed-length structure.
def _read_list_at(machO, position, method):
	if position:
		machO.seek(machO.fromVM(position))
		(_, count) = machO.readFormatStruct('2L')
		return [method(machO) for i in range(count)]
	else:
		return []


def readProtocols(protList, machO):
	"""Read a protocols pointed by the list of VM addresses."""

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
		(_, namePtr, protocolList, instMethodsPtr, classMethodsPtr, optInstMethodsPtr, optClassMethodsPtr, propsPtr) = machO.readFormatStruct('8^')
		
		machO.seek(machO.fromVM(namePtr))
		name = machO.readString()
		
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
			count = machO.readFormatStruct('^')[0]
			protoAddrs = machO.readFormatStruct(str(count) + '^')
			proto.addProtocols(protoDict[i][0] for i in protoAddrs)

	protos = {loc: _read_protocol_phase1(machO, loc) for loc in protList}
	for proto, protocolList in protos.values():
		_read_protocol_phase2(machO, proto, protocolList, protos)
	
	return {k: v[0] for k, v in protos.items()}
	

