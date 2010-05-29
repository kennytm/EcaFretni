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
from macho.utilities import fromStringz
from macho.macho import MachO
from factory import factory
from macho.sections.section import Section

class SegmentCommand(LoadCommand):
	"""The segment load command."""

	@property
	def segname(self):
		"""Get the segment name."""
		return self._segname

	@property
	def vmaddr(self):
		"""Get the base VM address of this segment."""
		return self._vmaddr

	def _loadSections(self, machO):
		is64bit = self._cmd == 'SEGMENT_64'
		
		(segname, self._vmaddr, self._vmsize, self._fileoff, self._filesize, _, _, nsects, _) = machO.readFormatStruct('16s4^2i2L', is64bit=is64bit)
		
		self._segname = fromStringz(segname)
		self._o = machO
		
		sections = {}
		for i in range(nsects):
			sect = Section.createSection(machO, is64bit)
			sections[sect.sectname] = sect
		self._sections = sections

	def analyze(self, machO):
		if not hasattr(self, '_sections'):
			self._loadSections(machO)
		
#		symtab = self.o.anyLoadCommand('SYMTAB')
#		if symtab is not None:
#			if not hasattr(symtab, 'symbols'):

		# analyze all sections.
		requiresAnalysis = {k:True for k in self._sections}
		while any(requiresAnalysis.values()):
			for k, s in self._sections.items():
				if requiresAnalysis[k]:
					machO.seek(s.offset)
					requiresAnalysis[k] = s.analyze(self, machO)
 

	def section(self, sectName):
		"""Get the section given the name."""
		return self._sections[sectName]
		
	def hasSection(self, sectName):
		"""Checks whether the specified section exists."""
		return sectName in self._sections
	
	
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
		val = self._o.readFormatStruct(fmt, is64bit=(self._cmd == 'SEGMENT_64'))
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

def _macho_segment(self, segname):
	"""Get the segment given its name"""
	for lc in self.allLoadCommands('SegmentCommand'):
		if lc.segname == segname:
			return lc
	return None

MachO.fromVM = _macho_forEachSegment('fromVM')
MachO.toVM = _macho_forEachSegment('toVM')
MachO.deref = _macho_forEachSegment('deref')
MachO.segment = _macho_segment

