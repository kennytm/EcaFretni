#
#	type.py ... Objective-C types
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

"""This module include all basic classes for Objective-C encodeable types."""

class Type(object):
	"""The base class to represent Objective-C encodeable type."""
	pass

class Prim(Type):
	"""Primitives types, such as 'int' and 'float'."""
	
	Class = '#'
	NXAtom = '%'
	Sel = ':'
	Bool = 'B'
	UnsignedChar = 'C'
	Unsigned = 'I'
	UnsignedLong = 'L'
	UnsignedLongLong = 'Q'
	UnsignedShort = 'S'
	Char = 'c'
	Double = 'd'
	Float = 'f'
	Int = 'i'
	Long = 'l'
	LongLong = 'q'
	Short = 's'
	Void = 'v'
	CharPtr = '*'
	FuncPtr = '^?'
	Block = '@?'
	
	validPrims = frozenset(['#','%',':','B','C','I','L','Q','S','c','d','f','i','l','q','s','v','*','^?','@?'])

	def __init__(self, primitive):
		self.primitive = primitive

class Unary(Type):
	"""Unary types, i.e. it add a fixed semantic to another type, such as 'T*' and 'const T'."""
	
	GCInvisible = '!'
	Pointer = '^'
	Inout = 'N'
	Bycopy = 'O'
	Byref = 'R'
	Oneway = 'V'
	Complex = 'j'
	In = 'n'
	Out = 'o'
	Const = 'r'
	
	validMods = frozenset(['!','^','N','O','R','V','j','n','o','r'])
	
	def __init__(self, modifier, typ):
		self.modifier = modifier
		self.typ = typ
	
class Array(Type):
	"""Array types."""

	def __init__(self, length, typ):
		self.length = length
		self.typ = typ

class Bitfield(Type):
	"""Bitfield type."""

	def __init__(self, size):
		self.size = size

class ObjCType(Type):
	"""Objective-C types, such as 'id' and 'NSString*'."""

	def __init__(self, name, protos=None):
		self.name = name
		self.protos = protos

class Struct(Type):
	"""Aggregate types, i.e. 'struct' and 'union'."""

	class Member(object):
		def __init__(self, typ, name=None):
			self.name = name
			self.typ = typ
	
	def __init__(self, name, members, isUnion=False):
		self.name = name
		self.members = members
		self.isUnion = isUnion

