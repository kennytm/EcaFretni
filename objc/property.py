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
			'D': ('sythesizedIvar', ''),
			'P': ('gcStrength', '__strong'),
			'W': ('gcStrength', '__weak'),
		}
		
		# attributes defined by a letter followed by some strings.
		__multiLetters = {
			'G': 'getter',
			'S': 'setter',
			'V': 'sythesizedIvar'
		}
		
		buffer = []
		for string in exploded:
			if buffer:
				buffer.append(string)
			else:
				typ = string[0]
				if typ in __multiLetters:
					setattr(self, __multiLetters[typ], string[1:])
				elif typ in __singleLetters:
					(attr, val) = __singleLetters[typ]
					setattr(self, attr, val)
				elif typ == 'T':
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
		self.atomic = True
		self.accessMethod = 'assign'
		self.readOnly = False
		self.sythesizedIvar = ''
		self.gcStrength = ''
		self._parseAttributes()
	
