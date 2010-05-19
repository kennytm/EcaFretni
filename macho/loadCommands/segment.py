#	
#	segment.py ... LC_SEGMENT load command.
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

from macho.macho import MachO, LoadCommand, MachOError
from macho.utilities import readFormatStruct, fromStringz
from collections import OrderedDict

class Section(object):
	"""A section."""
	
	def __init__(self, fn, endian, is64bit):
		(sectname, segname, self.addr, self.size,
			self.offset, self.align, reloff, nreloc, flags, rs1, rs2) = readFormatStruct(fn, '16s16s2^7L', endian, is64bit)
		rs3 = readFormatStruct(fn, 'L', endian, is64bit)[0] if is64bit else 0
		
		self.sectname = fromStringz(sectname)
		self.segname = fromStringz(segname)
		self.reserved = (None, rs1, rs2, rs3)
		
		self.type = flags & 0xff
		self.attrib = flags >> 8
	
	def __str__(self):
		return "<Section: {},{}. 0x{:x}/{:x}>".format(self.segname, self.sectname, self.addr, self.offset)

class SegmentCommand(LoadCommand):
	"""The segment load command."""

	def analyze(self):
		# LC_SEGMENT_64
		is64bit = self.cmd == 0x19
		
		(segname, self.vmaddr, _, fileoff, _, _, _, nsects, _) = readFormatStruct(self.o.file, '16s4^2i2L', self.o.endian, is64bit)
		
		self.segname = fromStringz(segname)
		self.vmdiff = self.vmaddr - fileoff
		
		sections = OrderedDict()
		for i in range(nsects):
			sect = Section(self.o.file, self.o.endian, is64bit)
			sections[sect.sectname] = sect
		self.sections = sections
	
	def __str__(self):
		return "<Segment: {} [{}]>".format(self.segname, ', '.join(map(str, self.sections.values())))


LoadCommand.registerFactory([1, 0x19], SegmentCommand)
		
