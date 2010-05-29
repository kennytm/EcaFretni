#
#	class_.py ... Describes an ObjC protocol
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

def Protocol(object):
	"""A structure representing an Objective-C protocol."""

	def __init__(self):
		self.requiredMethods = OrderedDict()	# method name as key.
		self.optionalMethods = OrderedDict()
		self.requiredClassMethods = OrderedDict()
		self.optionalClassMethods = OrderedDict()
		self.protocols = set()
		self.requiredProperties = OrderedDict()	# property name as key.
		self.optionalProperties = OrderedDict()
	
	def addMethod(self, method, isClassMethod=False, optional=False):
		"""Add a method to the class."""
		methodName = method.name
		if isClassMethod:
			if optional:
				self.optionalClassMethods[methodName] = method
			else:
				self.requiredClassMethods[methodName] = method
		else:
			if optional:
				self.optionalMethods[methodName] = method
			else:
				self.requiredMethods[methodName] = method
	
	def addProperty(self, prop, optional=False):
		"""Add a property to the class."""
		propName = property.name
		if optional:
			self.optionalProperties[propName] = prop
		else:
			self.requiredProperties[propName] = prop
	
	def addIvar(self, ivar):
		"""Add an ivar to the class."""
		self.ivars.append(ivar)
	
	def addProtocol(self, protocol):
		"""Add a protocol to the class."""
		self.protocols.add(protocol)
	
