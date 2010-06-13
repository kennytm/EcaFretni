#	
#	factory.py ... Factory pattern generator.
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
#	

'''

This module introduces the :func:`factory` class decorator, which can make a
class adopt the `factory pattern`_ distinguished by a keyword. Factories are 
registered at runtime, allowing plug-ins to provide extra capabilities without
modifying the base source code::

	@factory
	class Image(object):
	    def __init__(self, typ, width, height):
	        ...

	class PNGImage(Image):
	    ...
		
	class JPGImage(Image):
	    ...
		
	Image.registerFactory("png", PNGImage)
	Image.registerFactory("jpg", JPGImage)
	
	pngImg = Image.create("png", 100, 100)
	jpgImg = Image.create("jpg", 800, 600)
	genericImg = Image.create("gif", 20, 20)


.. _`factory pattern`: http://en.wikipedia.org/wiki/Factory_method_pattern

Patches
-------

The following class methods are added to a class adopting the :func:`factory`
decorator:

.. classmethod:: registerFactory(cls, keyword, cons)

	Register a keyword with a subclass *cons* of the class *cls*. The subclass's
	:meth:`__init__` method's signature should be::
	
		def __init__(self, keyword, ...):
		    ...

.. classmethod:: getFactory(cls, keyword)

	Returns the subclass registered with *keyword*. The base class *cls* will be
	returned if that keyword is unregistered.

.. classmethod:: create(cls, keyword, *args, **kargs)

	Create an instance, specialize to a subclass based on the *keyword*. 

Decorators
----------

'''


def factory(cls):
	"""A class decorator that enables factory pattern."""
	
	cls.__factories = {}
	
	@classmethod
	def registerFactory(cls, keyword, cons):
		"""Register a keyword with a constructor. See :mod:`factory` for detail."""
		cls.__factories[keyword] = cons
	
	cls.registerFactory = registerFactory
	
	@classmethod
	def getFactory(cls, keyword):
		"""Return the factory of a keyword. See :mod:`factory` for detail."""
		return cls.__factories.get(keyword, cls)
		
	cls.getFactory = getFactory
	
	@classmethod
	def create(cls, keyword, *args, **kargs):
		"""Create an instance by keyword. See :mod:`factory` for detail."""
		return cls.getFactory(keyword)(keyword, *args, **kargs)
	
	cls.create = create
	
	return cls



if __name__ == '__main__':
	@factory
	class A(object):
		def __init__(self, index, value):
			self.index = index
			self.value = value
			
		def __str__(self):
			return "{}: {}={}".format(type(self), self.index, self.value)
	
	class B(A):
		def __init__(self, index, value):
			super().__init__(index, value)
			print("constructing B")
	
	class C(A):
		def __init__(self, index, value):
			super().__init__(index, value)
			print("constructing C")
	
	A.registerFactory(4, B)
	A.registerFactory(7, B)
	A.registerFactory(6, C)
	
	print (A.create(3, 6))
	print (A.create(4, 7))
	print (A.create(5, 8))
	print (A.create(6, 9))
	print (A.create(7, 10))
	print (A.create(8, 11))
	
