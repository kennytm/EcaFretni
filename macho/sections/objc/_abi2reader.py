#
#	_abi2reader.py ... Read the Mach-O binary and parse into Objective-C stuff.
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

"""
Auxiliary module for reading Objective-C ABI 2.0 info.

.. seealso::

	`objc-private.h <http://www.opensource.apple.com/source/objc4/objc4-437.1/runtime/objc-private.h>`_
		Definition of some Objective-C related C structures.

	`objc-runtime-new.h <http://www.opensource.apple.com/source/objc4/objc4-437.1/runtime/objc-runtime-new.h>`_
		Definition of the Objective-C related C structures specific to ABI 2.0.

"""

from objc.class_ import Class, RemoteClass
from objc.method import Method
from objc.ivar import Ivar
from objc.property import Property
from objc.protocol import Protocol
from objc.category import Category
from macho.utilities import readStruct, peekStruct, peekStructs, peekPrimitives
from data_table import DataTable
import macho.loadcommands.segment	# to ensure macho.macho.MachO.[fromVM, derefString] are defined.



def readMethod(machO, optional):
	"""Read a ``method_t`` at current position to a :class:`~objc.method.Method`."""
	#	typedef struct method_t {
	#		SEL name;
	#		const char *types;
	#		IMP imp;
	#	} method_t;
	(namePtr, encPtr, imp) = readStruct(machO.file, machO.makeStruct('3^'))
	name = machO.derefString(namePtr)
	encoding = machO.derefString(encPtr)
	return Method(name, encoding, imp, optional)


def readIvar(machO):
	"""Read an ``ivar_t`` at current position to an :class:`~objc.ivar.Ivar`."""
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
	offset = machO.deref(offsetPtr, machO.makeStruct('^'))[0]
	name = machO.derefString(namePtr)
	encoding = machO.derefString(encPtr)
	return Ivar(name, encoding, offset)

def readProperty(machO):
	"""Read an ``objc_property`` at current position to a :class:`~objc.property.Property`."""
	#	struct objc_property {
	#		const char *name;
	#		const char *attributes;
	#	};
	(namePtr, attribPtr) = readStruct(machO.file, machO.makeStruct('2^'))
	name = machO.derefString(namePtr)
	attrib = machO.derefString(attribPtr)
	return Property(name, attrib)


# Just read any fixed-length structure.
def readListAt(method):
	"""
	Returns a function with signature::
	
		f(machO, vmaddr, *args, **kwargs)
	
	This function would read any continuous fixed-length structure at *vmaddr*,
	and analyze them with *method*. Returns a list in **reversed order**. If
	*vmaddr* is 0, an empty list is returned.
	
	This method has 3 specializations::
	
		readMethodListAt = readListAt(readMethod)
		readIvarListAt = readListAt(readIvar)
		readPropertyListAt = readListAt(readProperty)

	"""
	
	def f(machO, vmaddr, *args, **kwargs):
		if vmaddr:
			machO.seek(machO.fromVM(vmaddr))
			count = readStruct(machO.file, machO.makeStruct('2L'))[1]
			lst = [method(machO, *args, **kwargs) for _ in range(count)]
			lst.reverse()	# it is needed because the methods defined early will often appear later in the binary.
			return lst
		else:
			return []
			
	return f

readMethodListAt = readListAt(readMethod)
readIvarListAt = readListAt(readIvar)
readPropertyListAt = readListAt(readProperty)

def _readProtocolRefListAt(machO, vmaddr):
	"""Return the an iterable of addresses to protocols from *vmaddr*."""
	#	typedef struct protocol_list_t {
	#		// count is 64-bit by accident. 
	#		uintptr_t count;
	#		protocol_ref_t list[0]; // variable-size
	#	} protocol_list_t;
	if vmaddr:
		machO.seek(machO.fromVM(vmaddr))
		ptrStru = machO.makeStruct('^')
		count = readStruct(machO.file, ptrStru)[0]
		return peekPrimitives(machO.file, '^', count, machO.endian, machO.is64bit)
	else:
		return []

def readProtocol(machO, vmaddr):
	"""Peek a ``protocol_t`` at *offset*. Returns a tuple of
	:class:`~objc.protocol.Protocol` and an iterable of protocol addresses it is
	adopting."""

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
	
	pos = machO.fromVM(vmaddr) + machO.origin
	(_, namePtr, protocolListPtr, instMethodsPtr, classMethodsPtr, optInstMethodsPtr, optClassMethodsPtr, propsPtr) = peekStruct(machO.file, machO.makeStruct('8^'), position=pos)
	
	name = machO.derefString(namePtr)
	protocolRefs = _readProtocolRefListAt(machO, protocolListPtr)
	
	proto = Protocol(name)
	proto.addClassMethods(readMethodListAt(machO, classMethodsPtr, optional=False))
	proto.addClassMethods(readMethodListAt(machO, optClassMethodsPtr, optional=True))
	proto.addMethods(readMethodListAt(machO, instMethodsPtr, optional=False))
	proto.addMethods(readMethodListAt(machO, optInstMethodsPtr, optional=True))

	proto.addProperties(readPropertyListAt(machO, propsPtr))

	return (proto, protocolRefs)


def connectProtocol(obj, protocolRefs, protoRefsMap):
	"""Let *obj* adopts protocols referenced by the iterable *protocolRefs*,
	reading from the :class:`~data_table.DataTable` *protoRefsMap*."""
	obj.protocols.update(protoRefsMap.any1('addr', vmaddr) for vmaddr in protocolRefs)
	

def readProtocolList(machO, addresses):
	"""Read protocols from an iterable of *addresses*, and return a
	:class:`~data_table.DataTable` of :class:`~objc.protocol.Protocol`\\s with
	the following column names:
	
	* ``'name'`` (unique, string, the name of the protocol)
	* ``'addr'`` (unique, integer, the VM address to the protocol)
	"""
	
	# read protocols from the Mach-O binary.
	protos = DataTable('!name', '!addr')
	refs = []
	for vmaddr in addresses:
		(proto, protocolRefs) = readProtocol(machO, vmaddr)
		protos.append(proto, name=proto.name, addr=vmaddr)
		refs.append(protocolRefs)
	
	# connect the protocols.
	for proto, protocolRefs in zip(protos, refs):
		connectProtocol(proto, protocolRefs, protos)
		
	return protos


def _readClassRO(machO, cls, protoRefsMap, absfileoff):
	"""Peek a ``class_ro_t`` at *absfileoff*. If *cls* is ``None``, read the
	class as normal class. Otherwise, read as meta class and insert the class
	methods.
	"""

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
	
	(flags, _, _, _, namePtr, methodsPtr, protosPtr, ivarsPtr, _, propsPtr) = peekStruct(machO.file, machO.makeStruct('3L~7^'), position=absfileoff)
	
	methods = readMethodListAt(machO, methodsPtr, optional=False)
	
	if cls is None:
		# not meta class.
		
		name = machO.derefString(namePtr)
		cls = Class(name, flags)
		
		cls.addMethods(methods)
		cls.addIvars(readIvarListAt(machO, ivarsPtr))
		cls.addProperties(readPropertyListAt(machO, propsPtr))
		
		protocolRefs = _readProtocolRefListAt(machO, protosPtr)
		
		connectProtocol(cls, protocolRefs, protoRefsMap)
		
	else:
		# is meta-class: prepend the class methods.
		cls.addClassMethods(methods)
	
	return cls


def readClass(machO, vmaddr, protoRefsMap):
	"""Read a ``class_t`` at *vmaddr*, and returns a tuple of 
	:class:`~objc.class_.Class` and pointer (possibly relocated) to superclass,
	if any."""
	
	#	typedef struct class_t {
	#		struct class_t *isa;
	#		struct class_t *superclass;
	#		Cache cache;
	#		IMP *vtable;
	#		class_rw_t *data;
	#	} class_t;
	
	origin = machO.origin
	machO_fromVM = machO.fromVM
	
	classT = machO.makeStruct('5^')
	
	(metaPtr, superPtr, _, _, classRo) = peekStruct(machO.file, classT, position=machO_fromVM(vmaddr)+origin)
	
	cls = _readClassRO(machO, None, protoRefsMap, machO_fromVM(classRo)+origin)
	
	metaClassRo = peekStruct(machO.file, classT, position=machO_fromVM(metaPtr)+origin)[4]
	cls = _readClassRO(machO, cls, protoRefsMap, machO_fromVM(metaClassRo)+origin)
	
	# if the superclass is 0 but the class is not a root class, it is possible
	# that the superclass is an external class.
	if not superPtr and not cls.isRoot:
		superPtr = vmaddr + machO.pointerWidth
		
	return (cls, superPtr)


def classAt(machO, vmaddr, classes):
	'''Given a :class:`~data_table.DataTable` of :class:`~objc.class_.Class`\\s,
	get the :class:`~objc.class_.Class` or :class:`~objc.class_.RemoteClass` at
	the given *vmaddr*.'''
	
	cls = classes.any('addr', vmaddr)
	if not cls:
		sym = machO.symbols.any1('addr', vmaddr)
		cls = RemoteClass(sym)
	return cls



def readClassList(machO, addresses, protoRefsMap):
	"""Read classes from an iterable of *addresses*, and return a
	:class:`~data_table.DataTable` of :class:`~objc.class_.Class`\\s with
	the following column names:
	
	* ``'name'`` (unique, string, the name of the class)
	
	* ``'addr'`` (unique, integer, the VM address to the class)
	
	"""
		
	classes = DataTable('!name', '!addr')
	supers = []
	for vmaddr in addresses:
		(cls, superPtr) = readClass(machO, vmaddr, protoRefsMap)
		supers.append(superPtr)
		classes.append(cls, name=cls.name, addr=vmaddr)
	
	for cls, superPtr in zip(classes, supers):
		if not cls.isRoot:
			cls.superClass = classAt(machO, superPtr, classes)
	
	return classes
	

def readCategory(machO, vmaddr, classes, protoRefsMap):
	"""Read a ``category_t`` at *vmaddr*, and returns a tuple of 
	:class:`~objc.category.Category`, and the :class:`~objc.class_.Class` or
	:class:`~objc.class_.RemoteClass` it is patching."""

	#	typedef struct category_t {
	#		const char *name;
	#		struct class_t *cls;
	#		struct method_list_t *instanceMethods;
	#		struct method_list_t *classMethods;
	#		struct protocol_list_t *protocols;
	#		struct objc_property_list *instanceProperties;
	#	} category_t;
	
	pos = machO.fromVM(vmaddr) + machO.origin
	(namePtr, clsPtr, instMethodsPtr, classMethodsPtr, protosPtr, propsPtr) = peekStruct(machO.file, machO.makeStruct('6^'), position=pos)
		
	name = machO.derefString(namePtr)
	
	if not clsPtr:
		clsPtr = vmaddr + machO.pointerWidth
	cls = classAt(machO, clsPtr, classes)
	
	cat = Category(name, cls)
	cat.addClassMethods(readMethodListAt(machO, classMethodsPtr, optional=False))
	cat.addMethods(readMethodListAt(machO, instMethodsPtr, optional=False))
	cat.addProperties(readPropertyListAt(machO, propsPtr))
	
	protocolRefs = _readProtocolRefListAt(machO, protosPtr)
	connectProtocol(cat, protocolRefs, protoRefsMap)

	return cat


def readCategoryList(machO, addresses, classes, protoRefsMap):
	"""Read categories from an iterable of *addresses*, and return a
	:class:`~data_table.DataTable` of :class:`~objc.category.Category`\\s with
	the following column names:
	
	* ``'name'`` (string, the name of the category)
	* ``'base'`` (string, the name of the class the category is patching)
	"""
	
	cats = DataTable('name', 'base')
	for vmaddr in addresses:
		cat = readCategory(machO, vmaddr, classes, protoRefsMap)
		cats.append(cat, name=cat.name, base=cat.class_.name)
	
	return cats

	
	
