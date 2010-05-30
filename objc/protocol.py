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

class Protocol(object):
	"""A structure representing an Objective-C protocol."""

	def __init__(self, name, requiredMethods, optionalMethods, requiredClassMethods, optionalClassMethods, requiredProperties):
		self.name = name
		self.requiredMethods = OrderedDict((m.name, m) for m in requiredMethods)	# method name as key.
		self.optionalMethods = OrderedDict((m.name, m) for m in optionalMethods)
		self.requiredClassMethods = OrderedDict((m.name, m) for m in requiredClassMethods)
		self.optionalClassMethods = OrderedDict((m.name, m) for m in optionalClassMethods)
		self.protocols = set()
		self.requiredProperties = OrderedDict((p.name, p) for p in requiredProperties if p.getter in self.requiredMethods)	# property name as key.
		self.optionalProperties = OrderedDict((p.name, p) for p in requiredProperties if p.getter in self.optionalMethods)
	
	def __str__(self):
		protos = ' <{}>'.format(', '.join(p.name for p in self.protocols)) if self.protocols else ''
		reqMethods = ''.join("-{}\n".format(m) for m in self.requiredMethods.values())
		optMethods = ''.join("-{}\n".format(m) for m in self.optionalMethods.values())
		reqClsMethods = ''.join("+{}\n".format(m) for m in self.requiredClassMethods.values())
		optClsMethods = ''.join("+{}\n".format(m) for m in self.optionalClassMethods.values())
		reqProps = ''.join(str(p) + "\n" for p in self.requiredProperties.values())
		optProps = ''.join(str(p) + "\n" for p in self.optionalProperties.values())
		optionalText = "@optional\n" if optMethods or optClsMethods or optProps else ''
		return ''.join(["@protocol ", self.name, protos, "\n", reqProps, reqClsMethods, reqMethods, optionalText, optProps, optClsMethods, optMethods, "@end"])
		
	
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
	
	def addProtocols(self, protocols):
		"""Add a protocol to the class."""
		self.protocols.update(protocols)
	
