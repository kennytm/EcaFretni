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
from macho.utilities import fromStringz, peekStructs, peekString, readStruct
from macho.macho import MachO
from factory import factory
from macho.sections.section import Section
import macho.loadcommands.encryption_info	# ensures macho.macho.encrypted is defined.

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
		segStruct = machO.makeStruct('16s4^2i2L')
		sectStruct = machO.makeStruct(Section.STRUCT_FORMAT)
		(segname, self._vmaddr, self._vmsize, self._fileoff, self._filesize, _, _, nsects, _) = readStruct(machO.file, segStruct)
		
		self._segname = fromStringz(segname)
		self._o = machO
		
		sectVals = peekStructs(machO.file, sectStruct, count=nsects)	# get all section headers
		sectionsList = (Section.createSection(i) for i in sectVals)	# convert all headers into Section objects
		self._sections = {s.sectname: s for s in sectionsList}	# take the sectname and create a dict.
		self._hasAnalyzedSections = False


	def _analyzeSections(self, machO):
		# we need to make sure the section is not encrypted.
		requiresAnalysis = {n:not machO.encrypted(s.offset) for n, s in self._sections.items()}
		while any(requiresAnalysis.values()):
			for k, s in self._sections.items():
				if requiresAnalysis[k]:
					machO.seek(s.offset)
					requiresAnalysis[k] = s.analyze(self, machO)
		self._hasAnalyzedSections = True
		

	def analyze(self, machO):
		if not hasattr(self, '_sections'):
			self._loadSections(machO)
		
#		symtab = self.o.anyLoadCommand('SYMTAB')
#		if symtab is not None:
#			if not hasattr(symtab, 'symbols'):

		# make sure all segments are ready
		allSegments = machO.allLoadCommands(type(self).__name__)
		if any(not hasattr(seg, '_vmaddr') for seg in allSegments):
			return True
		
		if not self._hasAnalyzedSections:
			self._analyzeSections(machO)


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
			return -1
	
	def toVM(self, fileoff):
		"""Convert file offset to VM address. Returns None if out of range."""
		if self._fileoff <= fileoff < self._fileoff + self._filesize:
			return fileoff + self._vmaddr - self._fileoff
		else:
			return -1
	
	def deref(self, vmaddr, stru):
		fileoff = self._fromVM(vmaddr)
		if fileoff < 0:
			return None
		cur = self._o.tell()
		self._o.seek(fileoff)
		val = peekStruct(self._o.file, stru)
		self._o.seek(cur)
		return val
	
	def __str__(self):
		return "<Segment: {} [{}]>".format(self._segname, ', '.join(map(str, self._sections.values())))


LoadCommand.registerFactory('SEGMENT', SegmentCommand)
LoadCommand.registerFactory('SEGMENT_64', SegmentCommand)


def _macho_forEachSegment(func):
	def f(self, vmaddr):
		allAddrs = (func(lc, vmaddr) for lc in self.allLoadCommands('SegmentCommand'))
		try:
			return next(addr for addr in allAddrs if addr >= 0)
		except StopIteration:
			return -1
	return f

def _macho_deref(self, vmaddr, stru):
	"""Dereference a struct at vmaddr."""
	allDerefs = (lc.deref(vmaddr, stru) for lc in self.allLoadCommands('SegmentCommand'))
	try:
		return next(val for val in allDerefs if val is not None)
	except StopIteration:
		return None

def _macho_segment(self, segname):
	"""Get the segment given its name"""
	try:
		 return next(lc for lc in self.allLoadCommands('SegmentCommand') if lc.segname == segname)
	except StopIteration:
		return None

def _macho_derefString(self, vmaddr, encoding='utf_8', returnLength=False):
	"""Dereference a string."""
	offset = self.fromVM(vmaddr)
	cur = self.tell()
	self.seek(offset)
	res = peekString(self.file, encoding=encoding, returnLength=returnLength)
	self.seek(cur)
	return res


MachO.fromVM = _macho_forEachSegment(SegmentCommand.fromVM)
MachO.toVM = _macho_forEachSegment(SegmentCommand.toVM)
MachO.deref = _macho_deref
MachO.derefString = _macho_derefString
MachO.segment = _macho_segment

