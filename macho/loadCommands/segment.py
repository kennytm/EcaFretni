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

from macho.loadCommands.loadCommand import LoadCommand
from macho.utilities import readFormatStruct, fromStringz
from macho.macho import MachO
from factory import factory

@factory
class Section(object):
	"""An abstract section."""
	
	@classmethod
	def createSection(cls, fn, endian, is64bit):
		(sectname, segname, addr, size,
			offset, align, reloff, nreloc, flags, rs1, rs2) = readFormatStruct(fn, '16s16s2^7L', endian, is64bit)
		
		rs3 = readFormatStruct(fn, 'L', endian, is64bit)[0] if is64bit else 0
		
		sectname = fromStringz(sectname)
		segname = fromStringz(segname)
		reserved = (None, rs1, rs2, rs3)
		
		ftype = flags & 0xff
		attrib = flags >> 8
		
		return cls.create(sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved, fn, endian, is64bit)
	
	def __init__(self, sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved, fn, endian, is64bit):
		(self.sectname, self.segname, self.addr, self.size, self.offset,
			self.align, self.reloff, self.nreloc, self.ftype, self.attrib,
			self.reserved, self.fn, self.endian, self.is64bit) = (sectname,
				segname, addr, size, offset, align, reloff, nreloc, ftype,
				attrib, reserved, fn, endian, is64bit)
	
	def __str__(self):
		return "<Section: {},{}. 0x{:x}/{:x}>".format(self.segname, self.sectname, self.addr, self.offset)

class SegmentCommand(LoadCommand):
	"""The segment load command."""

	def __loadSections(self):
		is64bit = self.cmd == 'SEGMENT_64'
		
		(segname, self.vmaddr, self.vmsize, self.fileoff, self.filesize, _, _, nsects, _) = readFormatStruct(self.o.file, '16s4^2i2L', self.o.endian, is64bit)
		
		self.segname = fromStringz(segname)
		
		sections = {}
		for i in range(nsects):
			sect = Section.createSection(self.o.file, self.o.endian, is64bit)
			sections[sect.sectname] = sect
		self.sections = sections

	def analyze(self):
		if not hasattr(self, 'sections'):
			self.__loadSections()
			return True
		else:
			return False
		
			
	def fromVM(self, vmaddr):
		"""Convert VM address to file offset. Returns None if out of range."""
		if self.vmaddr <= vmaddr < self.vmaddr + self.vmsize:
			return vmaddr + self.fileoff - self.vmaddr
		else:
			return None
	
	def toVM(self, fileoff):
		"""Convert file offset to VM address. Returns None if out of range."""
		if self.fileoff <= fileoff < self.fileoff + self.filesize:
			return fileoff + self.vmaddr - self.fileoff
		else:
			return None
	
	def deref(self, vmaddr, fmt):
		fileoff = self.fromVM(vmaddr)
		if fileoff is None:
			return None
		self.fn.seek(fileoff)
		return readFormatStruct(self.fn, fmt, self.endian, self.is64bit)
	
	def __str__(self):
		return "<Segment: {} [{}]>".format(self.segname, ', '.join(map(str, self.sections.values())))


LoadCommand.registerFactory('SEGMENT', SegmentCommand)
LoadCommand.registerFactory('SEGMENT_64', SegmentCommand)


def __macho_forEachSegment(attrName):
	def f(self, addr):
		for lc in self.loadCommandClasses['SegmentCommand']:
			addr = getattr(lc, attrName)(vmaddr)
			if addr is not None:
				return addr
		return None
	return f

MachO.fromVM = __macho_forEachSegment('fromVM')
MachO.toVM = __macho_forEachSegment('toVM')
MachO.deref = __macho_forEachSegment('deref')
