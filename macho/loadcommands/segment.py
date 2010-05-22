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

from macho.loadcommands.loadcommand import LoadCommand
from macho.utilities import readFormatStruct, fromStringz
from macho.macho import MachO
from factory import factory

@factory
class Section(object):
	"""An abstract section."""
	
	@classmethod
	def createSection(cls, machO, is64bit):
		(sectname, segname, addr, size,
			offset, align, reloff, nreloc, flags, rs1, rs2) = machO.readFormatStruct('16s16s2^7L', is64bit=is64bit)
		
		rs3 = machO.readFormatStruct('L')[0] if is64bit else 0
		
		sectname = fromStringz(sectname)
		segname = fromStringz(segname)
		reserved = (None, rs1, rs2, rs3)
		
		ftype = flags & 0xff
		attrib = flags >> 8
		
		return cls.create(sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved, machO, is64bit)
	
	def __init__(self, sectname, segname, addr, size, offset, align, reloff, nreloc, ftype, attrib, reserved, machO, is64bit):
		(self.sectname, self.segname, self.addr, self.size, self.offset,
			self.align, self.reloff, self.nreloc, self.ftype, self.attrib,
			self.reserved, self._o, self._is64bit) = (sectname, segname, addr,
				size, offset, align, reloff, nreloc, ftype, attrib, reserved,
				machO, is64bit)
	
	def __str__(self):
		return "<Section: {},{}. 0x{:x}/{:x}>".format(self.segname, self.sectname, self.addr, self.offset)

class SegmentCommand(LoadCommand):
	"""The segment load command."""

	@property
	def segname(self):
		"""Get the segment name."""
		return self._segname

	def _loadSections(self):
		is64bit = self._cmd == 'SEGMENT_64'
		
		(segname, self._vmaddr, self._vmsize, self._fileoff, self._filesize, _, _, nsects, _) = self._o.readFormatStruct('16s4^2i2L', is64bit=is64bit)
		
		self._segname = fromStringz(segname)
		
		sections = {}
		for i in range(nsects):
			sect = Section.createSection(self._o, is64bit)
			sections[sect.sectname] = sect
		self._sections = sections

	def analyze(self):
		if not hasattr(self, 'sections'):
			self._loadSections()
		
#		symtab = self.o.anyLoadCommand('SYMTAB')
#		if symtab is not None:
#			if not hasattr(symtab, 'symbols'):

		
			
	def fromVM(self, vmaddr):
		"""Convert VM address to file offset. Returns None if out of range."""
		if self._vmaddr <= vmaddr < self._vmaddr + self._vmsize:
			return vmaddr + self._fileoff - self._vmaddr
		else:
			return None
	
	def toVM(self, fileoff):
		"""Convert file offset to VM address. Returns None if out of range."""
		if self._fileoff <= fileoff < self._fileoff + self._filesize:
			return fileoff + self._vmaddr - self._fileoff
		else:
			return None
	
	def deref(self, vmaddr, fmt):
		fileoff = self._fromVM(vmaddr)
		if fileoff is None:
			return None
		self._o.seek(fileoff)
		val = self._o.readFormatStruct(fmt, is64bit=self._is64bit)
		self._o.tell(fileoff)
		return val
	
	def __str__(self):
		return "<Segment: {} [{}]>".format(self._segname, ', '.join(map(str, self._sections.values())))


LoadCommand.registerFactory('SEGMENT', SegmentCommand)
LoadCommand.registerFactory('SEGMENT_64', SegmentCommand)


def _macho_forEachSegment(attrName):
	def f(self, addr):
		for lc in self.allLoadCommands('SegmentCommand'):
			addr = getattr(lc, attrName)(vmaddr)
			if addr is not None:
				return addr
		return None
	return f

MachO.fromVM = _macho_forEachSegment('fromVM')
MachO.toVM = _macho_forEachSegment('toVM')
MachO.deref = _macho_forEachSegment('deref')
