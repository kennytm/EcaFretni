#
#	category.py ... Describes an ObjC category
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

from collections import OrderedDict

def Category(object):
	"""A structure representing an Objective-C class."""

	def __init__(self, name):
		self.class_ = None
		self.name = name
		self.methods = OrderedDict()	# method name as key.
		self.classMethods = OrderedDict()
		self.protocols = set()
		self.properties = OrderedDict()	# property name as key.
			
	def addMethod(self, method, isClassMethod=False):
		"""Add a method to the category."""
		if isClassMethod:
			self.classMethods[method.name] = method
		else:
			self.methods[method.name] = method
	
	def addProperty(self, prop):
		"""Add a property to the category."""
		self.properties[property.name] = property
	
	def addProtocol(self, protocol):
		"""Add a protocol to the category."""
		self.protocols.add(protocol)
		
	