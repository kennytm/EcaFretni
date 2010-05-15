#
#	encode.py ... Convert Type class back into encoding strings
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

"""This module defines __str__ and __repr__ for Type to turn them into type encodings."""

from type.type import *

#-----------------

def __encodePrim(prim):
	return prim.primitive
def __reprPrim(prim):
	return 'Prim({!r})'.format(prim.primitive)

Prim.__str__ = __encodePrim
Prim.__repr__ = __reprPrim

#-----------------

def __encodeUnary(unary):
	return unary.modifier + str(unary.typ)
def __reprUnary(unary):
	return 'Unary({!r}, {!r})'.format(unary.modifier, unary.typ)

Unary.__str__ = __encodeUnary
Unary.__repr__ = __reprUnary

#-----------------

def __encodeArray(array):
	return '[{}{}]'.format(array.length, array.typ)
def __reprArray(array):
	return 'Array({!r}, {!r})'.format(array.length, array.typ)

Array.__str__ = __encodeArray
Array.__repr__ = __reprArray

#-----------------

def __encodeBitfield(bitfield):
	return 'b' + str(bitfield.size)
def __reprBitfield(bitfield):
	return 'Bitfield({!r})'.format(bitfield.size)

Bitfield.__str__ = __encodeBitfield
Bitfield.__repr__ = __reprBitfield

#-----------------

def __encodeObjCType(objc):
	if objc.name is None:
		if objc.protos is None:
			return '@'
		else:
			return '@"<{}>"'.format(','.join(sorted(objc.protos)))
	else:
		if objc.protos is None:
			return '@"{}"'.format(objc.name)
		else:
			return '@"{}<{}>"'.format(objc.name, ','.join(sorted(objc.protos)))

def __reprObjCType(objc):
	if objc.protos is None:
		return 'ObjCType({!r})'.format(objc.name)
	else
		return 'ObjCType({!r}, {!r})'.format(objc.name, objc.protos)

ObjCType.__str__ = __encodeObjCType
ObjCType.__repr__ = __reprObjCType

#-----------------

def __encodeStrMem(member):
	if member.name is None:
		return str(member.typ)
	else:
		return '"{}"{}'.format(member.name, member.typ)
def __reprStrMem(member):
	if member.name is None:
		return 'Struct.Member({!r})'.format(member.typ)
	else:
		return 'Struct.Member({!r}, {!r})'.format(member.typ, member.name)

Struct.Member.__str__ = __encodeStrMem
Struct.Member.__repr__ = __reprStrMem


def __encodeStruct(struct):
	(op, cl) = ('{', '}') if not struct.isUnion else ('(', ')')
	nm = struct.name or '?'
	if struct.members is not None:
		mems = '=' + ''.join(map(str, struct.members))
	else:
		mems = ''
	return ''.join((op, nm, mems, cl))
def __reprStruct(struct):
	fmt = 'Struct({!r}, {!r})' if not struct.isUnion else 'Struct({!r}, {!r}, isUnion=True)'
	return fmt.format(struct.name, struct.members)

Struct.__str__ = __encodeStruct
Struct.__repr__ = __reprStruct
	



