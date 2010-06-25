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
	stru = machO.makeStruct('I')
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
	*vmaddrs*."""
	
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




def analyzeProtocolList(machO, protoTuples):
	"""Analyze a list of protocols, and return a :class:`~data_table.DataTable`
	of :class:`~objc.protocol.Protocol`\\s with
	the following column names:
	
	* ``'name'`` (string, the name of the protocol)
	* ``'addr'`` (unique, integer, the VM address to the protocol)
	
	The parameter *protos* should be an iteratable of 2-tuples, which include
	the address of the protocol, and a 5-tuple representing an ``old_protocol``
	struct.
	"""
	
	# associate each unique protocol to a list of vmaddrs.
	protoDict = {}
	protoListDict = {}
	for vmaddr, protoTuple in protoTuples:
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


