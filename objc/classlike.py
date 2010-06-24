#
#	classlike.py ... Base class for all class-like objects.
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

from py2compat import OrderedDict


class ClassLike(object):
	"""This structure represents all class-like objects. A class-like object can
	have methods and adopt other protocols. There are 3 kinds of class-like
	objects in Objective-C:
	
	* :class:`objc.class_.Class`
	* :class:`objc.category.Category`
	* :class:`objc.protocol.Protocol`
	
	.. attribute:: name
	
		The name of this class-like object.
		
	.. attribute:: methods
	
		An ordered dictionary of :class:`~objc.method.Method`\ s as instance
		methods, keyed by the method name.
	
	.. attribute:: classMethods
	
		An ordered dictionary of :class:`~objc.method.Method`\ s as class
		methods, keyed by the method name.
	
	.. attribute:: protocols
	
		A set of :class:`~objc.protocol.Protocol`\ s adopted by this object.
	
	.. attribute:: properties
	
		A list of :class:`~objc.property.Property`\ s.
	
	"""
	
	def __init__(self, name):
		self.name = name
		self.methods = OrderedDict()
		self.classMethods = OrderedDict()
		self.protocols = set()
		self.properties = []
		
	def addMethods(self, methods):
		"""Add an iterable of *methods* to this class-like object."""
		self.methods.update((m.name, m) for m in methods)
	
	def addClassMethods(self, classMethods):
		"""Add an iterable of *classMethods* to this class-like object."""
		self.classMethods.update((m.name, m) for m in classMethods)
		
	def addProperties(self, properties):
		"""Add a sequence of *properties* to this class-like object.
		
		.. note::
		
			Make sure the corresponding getters and setters of the properties
			exist in this class-like object before calling this method.
		
		"""
		
		# By default properties do not have the sense of optionality. However, 
		# when a property is declared optional, its getter and setter will be
		# optional as well. Thus, by checking the optionality of the getter and
		# setter, the optionality of a property can be fixed.
		self_methods = self.methods
		for prop in properties:
			getter = prop.getter
			if getter in self_methods:
				prop.optional = self_methods[getter].optional
		self.properties.extend(properties)

	def stringify(self, prefix, middle, suffix):
		"""Stringify this class-like object. This should be used from the 
		``__str__`` method of its subclasses. These ``__str__`` methods are for
		debugging only. The result will look like::
		
			(prefix) name (middle) <protocols> (suffix)
			+classMethods
			-instMethods
			@end
			
		"""
	
		res = [prefix, self.name, middle]
		if self.protocols:
			res.append(' <')
			res.append(', '.join(p.name for p in self.protocols))
			res.append('> ')
		res.append(suffix)
		res.extend("\n" + str(m) for m in self.properties)
		res.extend("\n+" + str(m) for m in self.classMethods.values())
		res.extend("\n-" + str(m) for m in self.methods.values())
		res.append("\n@end\n")
		return ''.join(res)
