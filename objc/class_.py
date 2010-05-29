#
#	class_.py ... Describes an ObjC class
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

def Class(object):
	"""A structure representing an Objective-C class."""

	def __init__(self, name):
		self.superClass = None
		self.metaClass = None
		self.name = name
		self.isMeta = False
		self.isRoot = False
		self.hasStructors = False
		self.hidden = False
		self.exception = False
		self.methods = OrderedDict()	# method name as key.
		self.ivars = []
		self.protocols = set()
		self.properties = OrderedDict()	# property name as key.
	
	def parseFlag(self, flag):
		"""Parse a flag from ObjC 2 ABI."""
		self.isMeta = flag & 1
		self.isRoot = flag & 2
		self.hasStructors = flag & 4
		self.hidden = flag & 16
		self.exception = flag & 32
		
	def addMethod(self, method):
		"""Add a method to the class."""
		self.methods[method.name] = method
	
	def addProperty(self, prop):
		"""Add a property to the class."""
		self.properties[property.name] = property
	
	def addIvar(self, ivar):
		"""Add an ivar to the class."""
		self.ivars.append(ivar)
	
	def addProtocol(self, protocol):
		"""Add a protocol to the class."""
		self.protocols.add(protocol)
	
	def instanceMethod(self, methodName):
		"""Returns the specified instance method, including superclasses."""
		theClass = self
		while theClass:
			if methodName in theClass.methods:
				return theClass.methods[methodName]
			else:
				theClass = self.superClass
		return None
	
	def classMethod(self, methodName):
		"""Returns the specified class method, including superclasses."""
		if self.metaClass:
			return self.metaClass.instanceMethod(methodName)
		else:
			return None
		
	