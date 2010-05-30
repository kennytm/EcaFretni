#
#	method.py ... Describes an ObjC property
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

from balanced_substring import balancedSubstring

class Property(object):
	"""A structure representing an Objective-C property."""

	def _parseAttributes(self):
		index = 0
		exploded = self.attributes.split(',')
		
		# attributes defined by a single letter.
		__singleLetters = {
			'C': ('accessMethod', 'copy'),
			'&': ('accessMethod', 'retain'),
			'N': ('atomic', False),
			'D': ('synthesizedIvar', ''),
			'P': ('gcStrength', '__strong'),
			'W': ('gcStrength', '__weak'),
			'G': ('hasGetter', True),
			'S': ('hasSetter', True),
			'R': ('readOnly', True)
		}
		
		# attributes defined by a letter followed by some strings.
		__multiLetters = {
			'G': 'getter',
			'S': 'setter',
			'V': 'synthesizedIvar'
		}
		
		buffer = []
		for string in exploded:
			if buffer:
				buffer.append(string)
			else:
				typ = string[0]
				if typ in __multiLetters:
					setattr(self, __multiLetters[typ], string[1:])
				if typ in __singleLetters:
					(attr, val) = __singleLetters[typ]
					setattr(self, attr, val)
				if typ == 'T':
					buffer = [string[1:]]
			
			if buffer:
				joinedBuffer = ','.join(buffer)
				joinedBufferLength = len(joinedBuffer)
				if balancedSubstring(joinedBuffer) <= joinedBufferLength:
					self.encoding = joinedBuffer
					buffer = []


	def __init__(self, name, attributes):
		self.name = name
		self.attributes = attributes
		self.getter = name
		self.setter = 'set{}:'.format(name.capitalize())
		self.hasGetter = False
		self.hasSetter = False
		self.atomic = True
		self.accessMethod = 'assign'
		self.readOnly = False
		self.synthesizedIvar = ''
		self.gcStrength = ''
		self.encoding = ''
		self._parseAttributes()
	
	def attributeList(self):
		"""Return a list of attributes."""
		attribList = [self.accessMethod]
		if not self.atomic:
			attribList.append('nonatomic')
		if self.readOnly:
			attribList.append('readonly')
		if self.hasGetter:
			attribList.append('getter=' + self.getter)
		if self.hasSetter:
			attribList.append('setter=' + self.setter)
		return ', '.join(attribList)
	
	def __str__(self):
		res = '@property({}) {} {}[{}]'.format(self.attributeList(), self.name, self.gcStrength, self.encoding)
		if self.synthesizedIvar:
			res += ' = ' + self.synthesizedIvar
		return res + ';'
		
