#	
#	segment.py ... A section.
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

from factory import factory, factorySuffix
from macho.utilities import fromStringz, peekStructs, peekPrimitives, decodeStructFormat
from struct import calcsize
from hexdump import hexdump

(
	S_REGULAR,          # 0, regular section
	S_ZEROFILL,         # 1, zero fill on demand section
	S_CSTRING_LITERALS, # 2, section with only literal C strings
	S_4BYTE_LITERALS,   # 3, section with only 4 byte literals
	S_8BYTE_LITERALS,   # 4, section with only 8 byte literals
	S_LITERAL_POINTERS, # 5, section with only pointers to literals
	
	S_NON_LAZY_SYMBOL_POINTERS,   # 6, section with only non-lazy symbol pointers
	S_LAZY_SYMBOL_POINTERS,       # 7, section with only lazy symbol pointers
	S_SYMBOL_STUBS,               # 8, section with only symbol stubs, byte size of stub in the reserved2 field
	S_MOD_INIT_FUNC_POINTERS,     # 9, section with only function pointers for initialization
	S_MOD_TERM_FUNC_POINTERS,     # 10, section with only function pointers for termination
	S_COALESCED,                  # 11, section contains symbols that are to be coalesced
	S_GB_ZEROFILL,                # 12, zero fill on demand section (that can be larger than 4 gigabytes)
	S_INTERPOSING,                # 13, section with only pairs of function pointers for interposing
	S_16BYTE_LITERALS,            # 14, section with only 16 byte literals
	S_DTRACE_DOF,                 # 15, section contains DTrace Object Format
	S_LAZY_DYLIB_SYMBOL_POINTERS, # 16, section with only lazy symbol pointers to lazy loaded dylibs
	
	S_THREAD_LOCAL_REGULAR,                # 17, template of initial values for TLVs
	S_THREAD_LOCAL_ZEROFILL,               # 18, template of initial values for TLVs
	S_THREAD_LOCAL_VARIABLES,              # 19, TLV descriptors
	S_THREAD_LOCAL_VARIABLE_POINTERS,      # 20, pointers to TLV descriptors
	S_THREAD_LOCAL_INIT_FUNCTION_POINTERS, # 21, functions to call to initialize TLV values
	
) = range(22)

@factorySuffix(suffix='FType', defaultConstructor='byFType')
@factory
class Section(object):
	"""An abstract section.
	
	This class adopts the :func:`~factory.factory` class decorator. Subclasses
	should override the :meth:`analyze` method to collect data from the Mach-O
	file.
	
	.. attribute:: sectname
	
		Section name (e.g. ``'__cstring'``)
	
	.. attribute:: segname
	
		Segment name (e.g. ``'__TEXT'``)
	
	.. attribute:: addr
	
		The base VM address of this section.
	
	.. attribute:: size
	
		Size of this section.
	
	.. attribute:: offset
	
		File offset of this section.
	
	.. attribute:: align
	
		Alignment of this section.
	
	.. attribute:: reloff
		nreloc
		
		Relocation information.
	
	.. attribute:: ftype
	
		Section type, e.g. :const:`S_CSTRING_LITERALS`.
	
	.. attribute:: attrib
	
		Attributes of this section.
	
	.. attribute:: reserved
	
		A tuple of reserved information.
		
	.. attribute:: isAnalyzed
	
		Whether this section has been completely analyzed.
	
	"""
	
	STRUCT_FORMAT = '16s16s2^7L~'
	
	@classmethod
	def createSection(cls, val):
		'''Creates a section given be section header. *val* should be a tuple
		ordered as the C ``section`` structure.'''
	
		(sectname, segname, addr, size,
			offset, align, reloff, nreloc, flags, rs1, rs2) = val
		
		sectname = fromStringz(sectname)
		segname = fromStringz(segname)
		reserved = (rs1, rs2)
		
		ftype = flags & 0xff
		attrib = flags >> 8
			
		# we pass ftype twice to ensure __init__ and createSectionType won't be
		# mixed (as they have different number of arguments.)
		return cls.createFType(ftype, sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved)
	
	@classmethod
	def byFType(cls, ftype_kw, sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved):
		'''Create a section based on the section type. If a section is
		differentiated not just by sectname, the subclass should register the
		factory using::
		
			Section.registerFactoryFType(S_FOO, FooSection.byFType)
		'''
		cons = cls.create if cls is Section else cls
		return cons(sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved)
		
	def __init__(self, sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved):
		self.ftype = ftype
		self.sectname = sectname
		self.segname = segname
		self.addr = addr
		self.size = size
		self.offset = offset
		self.align = align
		self.reloff = reloff
		self.nreloc = nreloc
		self.attrib = attrib
		self.reserved = reserved
		self.isAnalyzed = False
				
	def analyze(self, segment, machO):
		"""Analyze the section.
		
		The file pointer is guaranteed to be at the desired offset and all
		segments are loaded when this method is called from
		:meth:`macho.loadcommands.segment.SegmentCommand.analyze`.
		
		Return a true value to require further analysis.
		"""
		
		return False
	
	def __str__(self):
		return "<{}: {},{}. 0x{:x}/{:x}>".format(type(self).__name__, self.segname, self.sectname, self.addr, self.offset)
		
#	def _read(self, o, length=None):
#		"""Read the whole section. For debugging only."""
#		o.seek(self.offset)
#		if length is None:
#			length = self.size
#		length = min(length, self.size)
#		return o._file.read(length)
#	
#	def _hexdump(self, o, length=None, visualizer='ascii'):
#		"""Hexdump the whole section. For debugging only."""
#		from hexdump import hexdump
#		hexdump(self._read(o, length), location=self.addr, visualizer=visualizer)
#	
	def asStructs(self, stru, machO, includeAddresses=False):
		"""Read the whole section as structs, and return an iterable of these.
		
		If *includeAddresses* is set to ``True``, return an iterable of
		(address, struct_content) tuples.
		"""
		
		count = self.size // stru.size
		structs = peekStructs(machO.file, stru, count=count, position=self.offset+machO.origin)
		
		if includeAddresses:		
			addrs = range(self.addr, self.addr + self.size, stru.size)	
			return zip(addrs, structs)
		else:
			return structs
	
	def asPrimitives(self, fmt, machO, includeAddresses=False):
		"""Read the whole section as primitives, and return an iterable of these.
		
		If *includeAddresses* is set to ``True``, return an iterable of
		(address, primitive) tuples.
		"""
		
		endian = machO.endian
		is64bit = machO.is64bit
		ssize = calcsize(decodeStructFormat(fmt, endian, is64bit))
		count = self.size // ssize
		prims = peekPrimitives(machO.file, fmt, count, endian, is64bit, position=self.offset+machO.origin)
		
		if includeAddresses:
			addrs = range(self.addr, self.addr + self.size, ssize)
			return zip(addrs, prims)
		else:
			return prims


	
		