#
#	method.py ... Describes an ObjC method
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

METHOD_ASSOC_NONE = 0
METHOD_ASSOC_DECLARED = 1
METHOD_ASSOC_NOUN = 2
METHOD_ASSOC_ADJECTIVE = 3
METHOD_ASSOC_IVAR = 4

class Method(object):
	"""A structure representing an Objective-C method.
	
	.. attribute:: name
	
		Name of this method, e.g. "initWithFoo:bar:".
	
	.. attribute:: imp
	
		VM address to implementation of this method. If there is no
		implementation, this value is 0.
	
	.. attribute:: encoding
	
		Raw type encoding of this method.
	
	.. attribute:: optional
	
		Whether this method is optional. Only useful for
		:class:`objc.protocol.Protocol`.
	
	.. attribute:: property
	
		The associated property of this method. 
	
	.. attribute:: propertyType
	
		How the property is associated to this method. It is an integer and can
		take one of these values:
		
		+--------------------------------+-------------------------------------+
		| Value                          | Meaning                             |
		+================================+=====================================+
		| ``METHOD_ASSOC_NONE`` (0)      | No associated properties.           |
		+--------------------------------+-------------------------------------+
		| ``METHOD_ASSOC_DECLARED`` (1)  | This method is a getter or setter   |
		|                                | of a declared property.             |
		+--------------------------------+-------------------------------------+
		| ``METHOD_ASSOC_NOUN`` (2)      | This method is associated to a      |
		|                                | property because both ``-noun`` and |
		|                                | ``-setNoun:`` exist.                |
		+--------------------------------+-------------------------------------+
		| ``METHOD_ASSOC_ADJECTIVE`` (3) | This method is associated to a      |
		|                                | property because both ``-isAdj``    |
		|                                | and ``-setAdj:`` exist, and it is a |
		|                                | ``BOOL``.                           |
		+--------------------------------+-------------------------------------+
		| ``METHOD_ASSOC_IVAR`` (4)      | This method is associated to a      |
		|                                | property because an ivar with the   |
		|                                | same name exists.                   |
		+--------------------------------+-------------------------------------+
	
	"""

	def __init__(self, name, encoding, imp, optional):
		self.name = name
		self.imp = imp
		self.encoding = encoding
		self.optional = optional
		self.property = None
		self.propertyType = METHOD_ASSOC_NONE
			
	def __str__(self):
		res = '{} [{}]'.format(self.name, self.encoding)
		if self.optional:
			res += ' @optional'
		if self.imp:
			res += ' / 0x{:x}'.format(self.imp)
		return res

