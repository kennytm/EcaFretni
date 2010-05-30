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

from factory import factory
from macho.utilities import fromStringz, peekStructs
from array import array

@factory
class Section(object):
	"""An abstract section."""
	
	STRUCT_FORMAT = '16s16s2^7L~'
	
	@classmethod
	def createSection(cls, val):
		(sectname, segname, addr, size,
			offset, align, reloff, nreloc, flags, rs1, rs2) = val
		
		sectname = fromStringz(sectname)
		segname = fromStringz(segname)
		reserved = (rs1, rs2)
		
		ftype = flags & 0xff
		attrib = flags >> 8
		
		return cls.create(sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved)
	
	def __init__(self, sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved):
		(self.sectname, self.segname, self.addr, self.size, self.offset,
			self.align, self.reloff, self.nreloc, self.ftype, self.attrib,
			self.reserved) = (sectname, segname, addr, size, offset, align,
				reloff, nreloc, ftype, attrib, reserved)
	
	def analyze(self, segment, machO):
		"""Analyze this section."""
		return False
	
	def __str__(self):
		return "<{}: {},{}. 0x{:x}/{:x}>".format(type(self).__name__, self.segname, self.sectname, self.addr, self.offset)
		
	def _read(self, o, length=None):
		"""Read the whole section. For debugging only."""
		o.seek(self.offset)
		if length is None:
			length = self.size
		length = min(length, self.size)
		return o._file.read(length)
	
	def _hexdump(self, o, length=None, visualizer='ascii'):
		"""Hexdump the whole section. For debugging only."""
		from hexdump import hexdump
		hexdump(self._read(o, length), location=self.addr, visualizer=visualizer)
	
	def peekStructs(self, stru, machO):
		"""Read the whole section as structs.
		
		Return an iterator of (address, struct_content) tuples.
		
		"""
		
		machO.seek(self.offset)
		count = self.size // stru.size
		structs = peekStructs(machO.file, stru, count=count)
		addrs = range(self.addr, self.addr + self.size, stru.size)
		
		return zip(addrs, structs)
	
		
	
		