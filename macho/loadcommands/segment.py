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
from macho.utilities import fromStringz, peekStructs, peekString, readStruct, peekStruct
from macho.macho import MachO
from factory import factory
from macho.sections.section import Section
from data_table import DataTable
from monkey_patching import patch
import struct

class SegmentCommand(LoadCommand):
	'''The segment load command. This can represent the 32-bit ``SEGMENT``
	command (``0x01``) or the 64-bit ``SEGMENT_64`` command  (``0x19``).
	
	A segment consists of many sections, which contain actual code and data.

	.. note::

		Sections falling in the encrypted region will not be analyzed if the
		:mod:`macho.loadcommands.encryption_info` module is imported.
		
	
	.. attribute:: segname
	
		Get the segment name.
	
	.. attribute:: vmaddr
	
		Get the base VM address of this segment.
	
	.. attribute:: sections
	
		A :class:`~data_table.DataTable` of all
		`~macho.sections.section.Section`\\s within this segment. This table 
		contains two columns: ``'className'`` and ``'sectname'``.
	
	'''

	def _loadSections(self, machO):
		segStruct = machO.makeStruct('16s4^2i2L')
		sectStruct = machO.makeStruct(Section.STRUCT_FORMAT)
		(segname, self.vmaddr, self._vmsize, self._fileoff, self._filesize, _, _, nsects, _) = readStruct(machO.file, segStruct)
		
		self.segname = fromStringz(segname)
		self._o = machO
		
		sectVals = peekStructs(machO.file, sectStruct, count=nsects)	# get all section headers
		sectionsList = (Section.createSection(i) for i in sectVals)	# convert all headers into Section objects
		sections = DataTable('className', 'sectname')
		for s in sectionsList:
			sections.append(s, className=type(s).__name__, sectname=s.sectname)
		self.sections = sections
		self._hasAnalyzedSections = False


	def _analyzeSections(self, machO):
		# we need to make sure the section is not encrypted.
		self_sections = self.sections
		machO_encrypted = getattr(machO, 'encrypted', lambda x: False)
		machO_seek = machO.seek
		
		requiresAnalysis = [not machO_encrypted(s.offset) for s in self_sections]
		while any(requiresAnalysis):
			for k, s in enumerate(self_sections):
				if requiresAnalysis[k]:
					machO_seek(s.offset)
					requiresAnalysis[k] = s.analyze(self, machO)
		self._hasAnalyzedSections = True
		

	def analyze(self, machO):
		if not hasattr(self, 'sections'):
			self._loadSections(machO)
		
		
		# make sure all segments are ready
		allSegments = machO.loadCommands.all('className', type(self).__name__)
		if any(not hasattr(seg, 'vmaddr') for seg in allSegments):
			return True
		
		if not self._hasAnalyzedSections:
			self._analyzeSections(machO)
	
	
	def fromVM(self, vmaddr):
		"""Convert VM address to file offset. Returns -1 if out of range."""
		if vmaddr > 0 and self.vmaddr <= vmaddr < self.vmaddr + self._vmsize:
			return vmaddr + self._fileoff - self.vmaddr
		else:
			return -1
	
	def toVM(self, fileoff):
		"""Convert file offset to VM address. Returns -1 if out of range."""
		if self._fileoff <= fileoff < self._fileoff + self._filesize:
			return fileoff + self.vmaddr - self._fileoff
		else:
			return -1
	
	def deref(self, vmaddr, stru):
		'''
		Dereference a structure at VM address *vmaddr*. The structure is defined
		by the :class:`struct.Struct` instance *stru*. Returns ``None`` if out
		of range.
		'''
		
		assert isinstance(stru, struct.Struct)
		
		fileoff = self.fromVM(vmaddr)
		if fileoff < 0:
			return None
		cur = self._o.tell()
		self._o.seek(fileoff)
		val = peekStruct(self._o.file, stru)
		self._o.seek(cur)
		return val
	
	def __str__(self):
		return "<Segment: {} [{}]>".format(self.segname, ', '.join(map(str, self._sections.values())))


LoadCommand.registerFactory('SEGMENT', SegmentCommand)
LoadCommand.registerFactory('SEGMENT_64', SegmentCommand)


@patch
class MachO_SegmentCommandPatches(MachO):
	"""This patch to the :class:`~macho.macho.MachO` class defines several
	methods that operate over all segments."""

	def segment(self, segname):
		"""Find a :class:`SegmentCommand` with the specified *segname*."""
		for segment in self.loadCommands.all('className', 'SegmentCommand'):
			if segment.segname == segname:
				return segment
		return None

	def fromVM(self, vmaddr):
		"""Convert a VM address to file offset. Returns -1 if the address does
		not exist."""
		for segment in self.loadCommands.all('className', 'SegmentCommand'):
			fileoff = segment.fromVM(vmaddr)
			if fileoff >= 0:
				return fileoff
		return -1

	def toVM(self, fileoff):
		"""Convert a file offset to VM address. Returns -1 if the address does
		not exist."""
		for segment in self.loadCommands.all('className', 'SegmentCommand'):
			vmaddr = segment.toVM(fileoff)
			if vmaddr >= 0:
				return vmaddr
		return -1

	def deref(self, vmaddr, stru):
		'''Dereference a structure at VM address *vmaddr*. The structure is
		defined by the :class:`~struct.Struct` instance *stru*. Returns ``None``
		if the address does not exist.'''
		for segment in self.loadCommands.all('className', 'SegmentCommand'):
			result = segment.deref(vmaddr, stru)
			if result:
				return result
		return None
	
	def derefString(self, vmaddr, encoding='utf_8', returnLength=False):
		'''Read a null-terminated string at VM address *vmaddr*. Returns
		``None`` if the address does not exist. See also
		:func:`macho.utilities.peekString` for meaning of other parameters.'''
		offset = self.fromVM(vmaddr)
		if offset < 0:
			return None
		cur = self.tell()
		self.seek(offset)
		res = peekString(self.file, encoding=encoding, returnLength=returnLength)
		self.seek(cur)
		return res
		
	def allSections(self, idtype, sectid):
		'''Returns an iterable of all :class:`~macho.sections.section.Section`\\s
		having the specified section identifier.
	
		If *idtype* is ``'sectname'``, then the *sectid* should be a section
		name, e.g. ``'__cstring'``.
	
		If *idtype* is ``'className'``, then the *sectid* should be the class
		name of the section to find, e.g. ``'CStringSection'``.'''
		
		for seg in self.loadCommands.all('className', 'SegmentCommand'):
			for sect in seg.sections.all(idtype, sectid):
				yield sect

	def anySection(self, idtype, sectid):
		'''Get any :class:`~macho.sections.section.Section` having the specified
		section identifier. Returns ``None`` if no such section exists.'''
		for sect in self.allSections(idtype, sectid):
			return sect
		return None
		