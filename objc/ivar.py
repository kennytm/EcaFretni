#
#	method.py ... Describes an ObjC ivar
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

class Ivar(object):
	"""A structure representing an Objective-C ivar.
	
	.. attribute:: name
	
		The name of this ivar.
	
	.. attribute:: offset
	
		Offset of this ivar in the instance.
		
	.. attribute:: encoding
	
		Type encoding of this ivar.
	
	.. attribute:: isPrivate
	
		Whether this ivar is a private one.
		
		If an ivar is private, its symbol will not be exported.
	
	"""

	def __init__(self, name, encoding, offset, isPrivate=False):
		self.name = name
		self.offset = offset
		self.encoding = encoding
		self.isPrivate = isPrivate
	
	def __str__(self):
		return '{} [{}] / 0x{:x}'.format(self.name, self.encoding, self.offset)
