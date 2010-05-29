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

def factory(cls):
	"""A class decorator that enables factory pattern.
	
	Usage:
	
		@factory
		class Base(object):
			def __init__(self, keyword, ...):
				...
	
		class D1(Base):
			...
			
		class D2(Base):
			...
			
		Base.registerFactory(1, D1)
		Base.registerFactory(2, D2)
		
		d1 = Base.create(1, ...)
		d2 = Base.create(2, ...)
		justBase = Base.create(3, ...)
	
	"""

	cls.__factories = {}
	
	@classmethod
	def registerFactory(cls, keyword, cons):
		"""Register a keyword with a constructor."""
		cls.__factories[keyword] = cons
	
	cls.registerFactory = registerFactory
	
	@classmethod
	def getFactory(cls, keyword):
		"""Return the factory of a keyword."""
		return cls.__factories.get(keyword, cls)
		
	cls.getFactory = getFactory
	
	@classmethod
	def create(cls, keyword, *args, **kargs):
		"""Create an instance by keyword"""
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
	
	