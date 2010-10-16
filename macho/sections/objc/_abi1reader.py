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
Auxiliary module for reading Objective-C ABI 1.0 info.

.. seealso::

	`objc-private.h <http://www.opensource.apple.com/source/objc4/objc4-437.1/runtime/objc-private.h>`_
		Definition of Objective-C ABI 1.0 C structures.

"""

from objc.class_ import Class, RemoteClass
from objc.method import Method
from objc.ivar import Ivar
from objc.property import Property
from objc.protocol import Protocol
from objc.category import Category
from macho.utilities import peekStruct, peekStructs, readStruct, peekPrimitives
from data_table import DataTable
from ._abi2reader import connectProtocol
from sym import SYMTYPE_UNDEFINED, Symbol


def methodDescriptionAnalyzer(d):
	"""Return a function which can convert a ``objc_method_description`` struct
	into a :class:`~objc.method.Method`.
	
	*d* should be set to ``machO.derefString``.
	"""
	
	def f(ptrs):
		#	struct objc_method_description {
		#		SEL name;
		#		char *types;
		#	};
		name = d(ptrs[0])
		types = d(ptrs[1])
		return Method(name, types, 0, False)
	
	return f
	
	
def prepareMethodDescriptionList(machO, vmaddr):
	"""Peek a ``objc_method_description_list`` struct at *vmaddr*, and return 
	the ``objc_method_description``\\s as an iterable of 2-tuples."""
	
	#	struct objc_method_description_list {
	#		int count;
	#		struct objc_method_description list[1];
	#	};

	if not vmaddr:
		return tuple()

	absfileoff = machO.fromVM(vmaddr) + machO.origin
	stru = machO.makeStruct('i')
	count = peekStruct(machO.file, stru, position=absfileoff)[0]	
	return peekStructs(machO.file, machO.makeStruct('2^'), count, position=absfileoff+stru.size)



def _prepareProtocol(machO, protoTuple):
	'''Convert an ``old_protocol`` struct to a tuple which can uniquely 
	identify a protocol, and can be used to construct an actual
	:class:`~objc.protocol.Protocol` object with :func:`_analyzeProtocol`.
	'''
	
	#	struct old_protocol {
	#		Class isa;
	#		const char *protocol_name;
	#		struct old_protocol_list *protocol_list;
	#		struct objc_method_description_list *instance_methods;
	#		struct objc_method_description_list *class_methods;
	#	};
	
	(_, namePtr, protoListPtr, instMethodsPtr, classMethodsPtr) = protoTuple
	
	# only instMethodsPtr & classMethodsPtr needs to be dereferenced.
	
	instMethods = tuple(prepareMethodDescriptionList(machO, instMethodsPtr))
	classMethods = tuple(prepareMethodDescriptionList(machO, classMethodsPtr))
	
	return ((namePtr, instMethods, classMethods), protoListPtr)



def _readProtocolRefListsAt(machO, vmaddrs):
	"""Return the an iterable of addresses to protocols from the iterable
	*vmaddrs* pointing to ``old_protocol_list``\\s."""
	
	#	struct old_protocol_list {
	#		struct old_protocol_list *next;
	#		long count;
	#		struct old_protocol *list[1];
	#	};
	
	f = machO.file
	stack = list(vmaddrs)
	
	while True:
		newStack = []
		for vmaddr in stack:
			machO.seek(machO.fromVM(vmaddr))
			(next, count) = readStruct(f, machO.makeStruct('2^'))
			if next:
				newStack.append(next)
			for addr in peekPrimitives(f, '^', count, machO.endian, machO.is64bit):
				yield addr
				
		if not newStack:
			break
		stack = newStack



def _analyzeProtocol(machO, d, analyzer, preped, protoListPtrs):
	"""Analyze a prepared ``old_protocol`` struct, and return a tuple of
	:class:`~objc.protocol.Protocol`\\s and an iterable of addresses of
	protocols it has adopted."""

	(namePtr, instMethods, classMethods) = preped
	
	name = d(namePtr)
	proto = Protocol(name)
	
	proto.addClassMethods(map(analyzer, reversed(classMethods)))
	proto.addMethods(map(analyzer, reversed(instMethods)))
	
	protocolRefs = _readProtocolRefListsAt(machO, protoListPtrs)
	
	return (proto, protocolRefs)
	


def analyzeProtocolList(machO, addressesAndProtoTuples):
	"""Analyze a list of protocols, and return a :class:`~data_table.DataTable`
	of :class:`~objc.protocol.Protocol`\\s with
	the following column names:
	
	* ``'name'`` (string, the name of the protocol)
	
	* ``'addr'`` (unique, integer, the VM address to the protocol)
	
	The parameter *addressesAndProtoTuples* should be an iteratable of 2-tuples,
	which include the VM address of the protocol, and a 5-tuple representing an
	``old_protocol`` struct.
	"""
	
	# associate each unique protocol to a list of vmaddrs.
	protoDict = {}
	protoListDict = {}
	for vmaddr, protoTuple in addressesAndProtoTuples:
		(preped, protoListPtr) = _prepareProtocol(machO, protoTuple)
		if preped in protoDict:
			protoDict[preped].append(vmaddr)
		else:
			protoDict[preped] = [vmaddr]
		if protoListPtr:
			if preped in protoListDict:
				protoListDict[preped].append(protoListPtr)
			else:
				protoListDict[preped] = [protoListPtr]
	
	# now do the actual analysis.
	protos = DataTable('name', '!addr')	# there can be multiple protocols with the same name in ABI 1.0
	refs = []
	d = machO.derefString
	analyzer = methodDescriptionAnalyzer(d)
	for preped, vmaddrs in protoDict.items():
		protoListPtrs = protoListDict[preped] if preped in protoListDict else []
		(proto, protoRefs) = _analyzeProtocol(machO, d, analyzer, preped, protoListPtrs)
		protos.append(proto, name=proto.name)
		protos.associate(proto, 'addr', vmaddrs)
		refs.append(protoRefs)

	# connect the protocols.
	for proto, protocolRefs in zip(protos, refs):
		connectProtocol(proto, protocolRefs, protos)
		
	return protos


def analyzeIvar(machO, ivarTuple):
	"""Analyze an ``old_ivar`` struct and return an :class:`~objc.ivar.Ivar`."""
	d = machO.derefString
	name = d(ivarTuple[0])
	typenc = d(ivarTuple[1])
	offset = ivarTuple[2]
	return Ivar(name, typenc, offset)
	
	
def analyzeMethod(machO, methodTuple):
	"""Analyze an ``old_method`` struct and return a
	:class:`~objc.method.Method`."""
	d = machO.derefString
	name = d(methodTuple[0])
	typenc = d(methodTuple[1])
	imp = methodTuple[2]
	return Method(name, typenc, imp, False)


def analyzeProperty(machO, propertyTuple):
	"""Analyze an ``objc_property`` struct and return a
	:class:`~objc.property.Property`."""
	d = machO.derefString
	name = d(propertyTuple[0])
	attrib = d(propertyTuple[1])
	return Property(name, attrib)


def listReader(method, fmt1, fmt2):
	"""
	Returns a function with signature::
	
		f(machO, vmaddr)
	
	This function would read any continuous fixed-length structure *fmt2* at
	*vmaddr*, and analyze them with *method*. Returns a list in **reversed
	order**. If *vmaddr* is 0, an empty list is returned.
	
	This method has 3 specializations::
	
		readMethodList = listReader(analyzeMethod, '^I~', '3^')
		readIvarList = listReader(analyzeIvar, 'I~', '2^I~')
		readPropertyList = listReader(analyzeProperty, '?')

	"""
	def f(machO, vmaddr):
		if not vmaddr:
			return []
	
		f = machO.file
		ms = machO.makeStruct
		pos = machO.fromVM(vmaddr) + machO.origin
		stru = ms(fmt1)
		count = peekStruct(f, stru, position=pos)[-1]						# use fmt1 to obtain the count
		tuples = peekStructs(f, ms(fmt2), count, position=pos+stru.size)	# use fmt2 to obtain the structures
		lst = [method(machO, s) for s in tuples]
		lst.reverse()
		return lst
		
	return f

readMethodList = listReader(analyzeMethod, '^I~', '3^')
readIvarList = listReader(analyzeIvar, 'I~', '2^I~')
readPropertyList = listReader(analyzeProperty, '2L', '2^')


def readLists(machO, vmaddr, method):
	"""Read a senital-terminated list at *vmaddr* using *method*, and
	concatenate the result.
	
	*method* should have signature::
	
		f(machO, vmaddr)

	and returns an iterable.
	"""

	#	struct old_method {
	#		SEL method_name;
	#		char *method_types;
	#		IMP method_imp;
	#	};
	#
	#	struct old_method_list {
	#		struct old_method_list *obsolete;
	#
	#		int method_count;
	#	#ifdef __LP64__
	#		int space;
	#	#endif
	#		/* variable length structure */
	#		struct old_method method_list[1];
	#	};
	
	retval = []
	
	if vmaddr:
		loc = machO.origin + machO.fromVM(vmaddr)
		stru = machO.makeStruct('^')
		ptrSize = stru.size
		f = machO.file
		while True:
			ptr = peekStruct(f, stru, position=loc)[0]
			if ptr > 0:
				retval.extend(method(machO, ptr))
			else:
				break
			loc += ptrSize
			
	return retval


def analyzeClass(machO, classTuple, protoRefsMap):
	"""Analyze an ``old_class`` structure.
		
	Returns the :class:`~objc.class_.Class` and the pointer to the super class.
	"""

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
	
	(metaClsPtr, superClsPtr, namePtr, _, _, _, ivarListPtr, methodListsPtr, _, protoListPtr, _, classExtPtr) = classTuple
	
	ms = machO.makeStruct
	deref = machO.deref
	
	name = machO.derefString(namePtr)
	cls = Class(name)
	
	cls.addIvars(readIvarList(machO, ivarListPtr))
	cls.addMethods(readLists(machO, methodListsPtr, readMethodList))
	
	if protoListPtr:
		protoAddrs = list(_readProtocolRefListsAt(machO, [protoListPtr]))
		connectProtocol(cls, protoAddrs, protoRefsMap)
	
	if classExtPtr:
		#	struct old_class_ext {
		#		uint32_t size;
		#		const char *weak_ivar_layout;
		#		struct objc_property_list **propertyLists;
		#	};
		propListsPtr = deref(classExtPtr, ms('L~2^'))[2]
		cls.addProperties(readPropertyList(machO, propListsPtr))
	
	metaClsTuple = deref(metaClsPtr, ms('12^'))
	cls.addClassMethods(readLists(machO, metaClsTuple[7], readMethodList))
	
	return (cls, superClsPtr)
	

def classAt(machO, vmaddr, classes):
	'''Given a :class:`~data_table.DataTable` of :class:`~objc.class_.Class`\\s,
	get the :class:`~objc.class_.Class` or :class:`~objc.class_.RemoteClass` at
	the given *vmaddr*.'''
	
	cls = classes.any('addr', vmaddr)
	if not cls:
		nm = machO.symbols.any1('addr', vmaddr)
		cls = RemoteClass(nm)
	return cls




def analyzeClassList(machO, addressesAndClassTuples, protocols):
	"""Analyze a list of classes, and return a :class:`~data_table.DataTable` of
	:class:`~objc.class_.Class`\\s with the following column names:
	
	* ``'name'`` (unique, string, the name of the class)
	
	* ``'addr'`` (unique, integer, the VM address to the class)
	
	The parameter *addressesAndClassTuples* should be an iteratable of 2-tuples,
	which include the VM address of the class, and a 12-tuple representing an
	``old_class`` struct.
	"""

	classes = DataTable('!name', '!addr')
	supers = []
	for vmaddr, classTuple in addressesAndClassTuples:
		(cls, superPtr) = analyzeClass(machO, classTuple, protocols)
		supers.append(superPtr)
		classes.append(cls, name=cls.name, addr=vmaddr)
	
	for cls, superPtr in zip(classes, supers):
		if superPtr:
			supcls = classAt(machO, superPtr, classes)
			cls.superClass = classAt(machO, superPtr, classes)
	
	return classes




def analyzeCategory(machO, catTuple, classes, protoRefsMap):
	"""Analyze an ``old_category`` structure, and returns the
	:class:`~objc.category.Category`"""
	
	#	struct old_category {
	#	    char *category_name;
	#	    char *class_name;
	#	    struct old_method_list *instance_methods;
	#	    struct old_method_list *class_methods;
	#	    struct old_protocol_list *protocols;
	#	    uint32_t size;
	#	    struct objc_property_list *instance_properties;
	#	};

	(namePtr, clsNamePtr, methodListsPtr, clsMethodListsPtr, protoListPtr, _, propListsPtr) = catTuple
	
	ds = machO.derefString
	
	name = ds(namePtr)
	clsName = ds(clsNamePtr)
	
	cls = classes.any('name', clsName)
	if not cls:
		newSymbol = machO.symbols.any1('addr', clsNamePtr)
		cls = RemoteClass(newSymbol)
	
	cat = Category(name, cls)
	cat.addMethods(readMethodList(machO, methodListsPtr))
	cat.addClassMethods(readMethodList(machO, clsMethodListsPtr))
	if protoListPtr:
		protoAddrs = list(_readProtocolRefListsAt(machO, [protoListPtr]))
		connectProtocol(cat, protoAddrs, protoRefsMap)	
	
	cls.addProperties(readPropertyList(machO, propListsPtr))
	
	return cat


def analyzeCategoryList(machO, catTuples, classes, protocols):
	"""Analyze a list of classes, and return a :class:`~data_table.DataTable` of
	:class:`~objc.class_.Class`\\s with the following column names:
	
	* ``'name'`` (string, the name of the category)
	
	* ``'base'`` (string, the name of the class the category is patching)
	
	The parameter *catTuples* should be an iteratable of 7-tuples representing
	the ``old_category`` structs.
	"""

	cats = DataTable('name', 'base')
	for catTuple in catTuples:
		cat = analyzeCategory(machO, catTuple, classes, protocols)
		cats.append(cat, name=cat.name, base=cat.class_.name)
	
	return cats
