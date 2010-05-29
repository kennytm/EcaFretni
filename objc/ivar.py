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

def Ivar(object):
	"""A structure representing an Objective-C ivar."""

	def __init__(self, name, offset, encoding, isPrivate=False):
		self.name = name
		self.offset = offset
		self.encoding = encoding
		self.isPrivate = isPrivate
	
