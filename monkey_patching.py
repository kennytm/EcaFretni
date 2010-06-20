#	
#	monkey_patching.py ... Monkey patching a class.
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

import sys

class MonkeyPatchingError(Exception):
	def __init__(self, message): self._msg = message
	def __str__(self): return self._msg


class DuplicatedMethodError(MonkeyPatchingError):
	'''This exception is raised when a method attempted to define conflicts with
	an existing one.'''
	def __init__(self, baseClassName, subclassName, methodName):
		super().__init__("Cannot monkey patch base class '{}' by '{}',"
		                 "because the method '{}' already exists".format(
		                     baseClassName, subclassName, methodName))


class MultipleInheritanceError(MonkeyPatchingError):
	'''This exception is raised when the class to monkey patch has multiple 
	superclasses.'''
	def __init__(self, subclassName):
		super().__init__("The subclass '{}' has multiple superclasses.".format(subclassName))


if 'sphinx-build' in sys.argv[0]:
	def patch(cls):
		'''This class decorator turns a subclass into a
		`monkey-patching <http://en.wikipedia.org/wiki/Monkey_patch>`_ group::
		
			class Foo(object):
				pass
			
			@patch
			class FooPrinter(Foo):
				def show(self):
					print('{}.show'.format(type(self)))
			
			f = Foo()
			f.show()
			# prints "<class '__main__.Foo'>.show"
		
		To monkey-patch a class X, the subclass should inherit X. All public
		methods will be dynamically added to class X. The method should not
		already exists, otherwise a :exc:`DuplicatedMethodError` will be raised.
		
		.. note::
		
			Private methods (``_foo``) and special methods (``__foo__``) are
			*not* added to the base class.
		
		Applying this decorator will make the it a synonym of the patched class.
		'''
		
		cls.sphinx_monkeyPatched = True
		return cls

else:
	def patch(cls):
		'''This class decorator turns a subclass into a monkey-patching group.'''
		if len(cls.__bases__) != 1:
			raise MultipleInheritanceError(cls.__name__)
		
		the_base = cls.__bases__[0]
		for name, method in cls.__dict__.items():
			# Do not import private methods.
			if name[0] != '_':
				if hasattr(the_base, name):
					raise DuplicatedMethodError(the_base.__name__, cls.__name__, name)
				setattr(the_base, name, method)
				
		return the_base
		

if __name__ == '__main__':
	class A(object):
		pass
	
	class B(A):
		def foo(self):
			pass
	
	@patch
	class C(B):
		def bar(self):
			pass
	
	assert C == B
	assert hasattr(B, 'bar')
	assert not hasattr(A, 'bar')
	
	@patch
	class D(B):
		def baz(self):
			pass
	
	assert D == C
	assert hasattr(B, 'baz')
	assert not hasattr(A, 'baz')
	
	@patch
	class E(A):
		def qux(self):
			pass
			
	assert E == A
	assert E != D
	assert hasattr(A, 'qux')
	assert hasattr(B, 'qux')
	
	exceptionRaised = False
	try:
		class I(object):
			pass
	
		@patch
		class F(A, I):
			pass
	except MultipleInheritanceError:
		exceptionRaised = True
	assert exceptionRaised
	
	exceptionRaised = False
	try:
		@patch
		class G(B):
			def bar(self):
				pass
	except DuplicatedMethodError:
		exceptionRaised = True
	assert exceptionRaised
	
	exceptionRaised = False
	try:
		@patch
		class H(B):
			def foo(self):
				pass
	except DuplicatedMethodError:
		exceptionRaised = True
	assert exceptionRaised
	
