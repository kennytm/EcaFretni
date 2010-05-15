#
#	parse.py ... Parse ObjC type encoding into classes.
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

"""This module parses an Objective-C encoded type string into Types."""

from type.type import *
from balancedSubstring import *
import re

class __Parser(object):
	"""The type string parser. Should not be used in public."""
	
	_digitsRx     = re.compile(r"\d+")
	_objcRx       = re.compile('@(?:"([^<"]*)(?:<([^>]+)>)?")?')
	_objcNamedRx  = re.compile('@(?:"([^<"]*)(?:<([^>]+)>)?"(?=["})]))?')
	_strNameRx    = re.compile('"([^"]+)"')


	def __init__(self, string):
		self.string = string
		self.index = 0
		
	
	def parsePrim(self):
		enc = self.string[self.index:self.index+2]
		if enc in Prim.validPrims:
			self.index += 2
			return Prim(enc)
		else:
			enc = self.string[self.index]
			if enc in Prim.validPrims:
				self.index += 1
				return Prim(enc)
			else:
				return None

	
	def parseUnary(self):
		enc = self.string[self.index]
		if enc in Unary.validMods:
			self.index += 1
			typ = self.parseType()
			
			# Be lenient if a pointer is not followed by a valid type.
			# it's likely just a funcptr.
			if typ is None and enc == Unary.Pointer:
				return Prim(Prim.FuncPtr)
			
			return Unary(enc, typ)
		else:
			return None
	
	
	def parseBitfield(self):
		if self.string[self.index] != 'b':
			return None
			
		m = self._digitsRx.match(self.string, self.index+1)
		self.index = m.end()
		return Bitfield(int(m.group()))
	
	
	def parseArray(self):
		if self.string[self.index] != '[':
			return None
		
		m = self._digitsRx.match(self.string, self.index+1)
		self.index = m.end()
		length = int(m.group())
		typ = self.parseType()
		self.index += 1
		
		return Array(length, typ)
	
	
	# Choose _objcRx or _objcNamedRx as the argument depending on the scope.
	def parseObjCType(self, rx=None):
		if rx is None:
			rx = self._objcRx
	
		m = rx.match(self.string, self.index)
		if m is None:
			return None
		self.index = m.end()
		name = m.group(1)
		protos = m.group(2)
		if name == '':
			name = None
		if protos is not None:
			protos = set(protos.split(','))
		return ObjCType(name, protos)
		
		
	def parseStructMembers(self):
		members = []
		while self.string[self.index] not in ')}':
			typ = self.parseType()
			if typ is None:
				break
			members.append(Struct.Member(typ))
		return members
	
	
	def parseNamedStructMembers(self):
		members = []
		while self.string[self.index] not in ')}':
			m = self._strNameRx.match(self.string, self.index)
			name = None
			if m is not None:
				name = m.group(1)
				self.index = m.end()
			
			typ = self.parseType(self._objcNamedRx)
			if typ is None:
				break
				
			members.append(Struct.Member(typ, name))
			
		return members

	
	def parseStruct(self):
		if self.string[self.index] not in '({':
			return None
		
		isUnion = self.string[self.index] == '('
		
		# 1. Extract the name.
		self.index += 1
		oldIndex = self.index
		while self.string[self.index] not in '=)}':
			self.index = balancedSubstring(self.string, self.index)
		name = self.string[oldIndex:self.index]
		if name == '?':
			name = None
		
		# 2. Extract members.
		if self.string[self.index] == '=':
			members = []
			self.index += 1
			if self.string[self.index] == '"':
				members = self.parseNamedStructMembers()
			else:
				members = self.parseStructMembers()
		else:
			members = None
	
		self.index += 1
	
		return Struct(name, members, isUnion)
		
		
	def parseType(self, objcRx=None):
		if objcRx is None:
			objcRx = self._objcRx
		
		parserMethods = [
			self.parsePrim,
			self.parseUnary,
			self.parseBitfield, 
			self.parseArray,
			self.parseStruct]
		
		for m in parserMethods:
			typ = m()
			if typ is not None:
				return typ
		
		return self.parseObjCType(objcRx)



def parse(encoding):
	"""Parse an Objective-C type encoding string into Types."""
	
	p = __Parser(encoding)
	return p.parseType()


