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

from .classlike import ClassLike
from collections import OrderedDict
from sym import SYMTYPE_UNDEFINED

class Class(ClassLike):
	"""A structure representing an Objective-C class.
	
	.. attribute:: superClass
	
		The :class:`~objc.classlike.ClassLike` object for this class's super
		class. If this class is the root class, its value is ``None``.
	
	.. attribute:: ivars
	
		An :class:`~collections.OrderedDict` of :class:`~objc.ivar.Ivar`\ s,
		keyed by the ivar name.
	
	.. attribute:: isRoot
	
		Whether this class is a root class.
	
	.. attribute:: hasStructors
	
		Whether this class has C++ constructors or destructors.
	
	.. attribute:: hidden
	
		Whether this class has been declared ``__attribute__((hidden))``.
	
	.. attribute:: exception
	
		Whether this class is an exception.
	
	"""

	def __init__(self, name, flags=0):
		super().__init__(name)
		self.superClass = None
		self.ivars = OrderedDict()
		self.parseFlags(flags)
	
	def parseFlags(self, flag):
		"""Parse a flag from ObjC 2 ABI."""
		self.isMeta = flag & 1
		self.isRoot = flag & 2
		self.hasStructors = flag & 4
		self.hidden = flag & 16
		self.exception = flag & 32
	
	def addIvars(self, ivars):
		"""Add an iterable of *ivars* into this class."""
		self.ivars.update((v.name, v) for v in ivars)
	
	def __str__(self):
		if self.superClass:
			middle = " : " + self.superClass.name
		else:
			middle = ""
		suffix = [" {\n"]
		suffix.extend("\t" + str(iv) + "\n" for iv in self.ivars.values())
		suffix.append('}')
		return self.stringify('@interface ', middle, ''.join(suffix))
		

class RemoteClass(ClassLike):
	"""A structure representing an external class."""
	def __init__(self, symbol):
		name = symbol.name
		if symbol.symtype == SYMTYPE_UNDEFINED:
			name = name[14:]
		
		super().__init__(name)
		self.symbol = symbol
