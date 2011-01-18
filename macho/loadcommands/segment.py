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

from macho.loadcommands.loadcommand import LoadCommand, LC_SEGMENT, LC_SEGMENT_64
from macho.utilities import fromStringz, peekStructs, peekString, readStruct, peekStruct
from macho.macho import MachO
from factory import factory
from macho.sections.section import Section, S_ZEROFILL, S_GB_ZEROFILL, S_THREAD_LOCAL_ZEROFILL
from data_table import DataTable
from monkey_patching import patch
from macho.vmaddr import Mapping
import struct

class SegmentCommand(LoadCommand):
	'''The segment load command. This can represent the 32-bit
	:const:`~macho.loadcommands.loadcommand.LC_SEGMENT` command (``0x01``) or
	the 64-bit :const:`~macho.loadcommands.loadcommand.LC_SEGMENT_64` command
	(``0x19``).
	
	A segment consists of many sections, which contain actual code and data.

	.. note::

		Sections falling in the encrypted region will not be analyzed if the
		:mod:`macho.loadcommands.encryption_info` module is imported.
		
	
	.. attribute:: segname
	
		Get the segment name.
	
	.. attribute:: vmaddr
	
		Get the base VM address of this segment.
	
	.. attribute:: maxprot
	
		Maximum VM protection of this segment when mapped to memory.
	
	.. attribute:: initprot
	
		Initial VM protection of this segment when mapped to memory.
	
	.. attribute:: sections
	
		A :class:`~data_table.DataTable` of all
		:class:`~macho.sections.section.Section`\\s within this segment. This
		table contains two columns: ``'className'`` and ``'sectname'``.
	
	'''

	def _loadSections(self, machO):
		segStruct = machO.makeStruct('16s4^2i2L')
		sectStruct = machO.makeStruct(Section.STRUCT_FORMAT)
		(segname, self.vmaddr, self._vmsize, self._fileoff, self._filesize, self.maxprot, self.initprot, nsects, _) = readStruct(machO.file, segStruct)
		
		self.segname = fromStringz(segname)
		
		machO_fileOrigin = machO._fileOrigin
			
		sectVals = peekStructs(machO.file, sectStruct, count=nsects)	# get all section headers
		sectionsList = (Section.createSection(i) for i in sectVals)	# convert all headers into Section objects
		sections = DataTable('className', 'sectname', 'ftype')
		for s in sectionsList:
			if s.offset < machO_fileOrigin:
				s.offset += machO_fileOrigin
			sections.append(s, className=type(s).__name__, sectname=s.sectname, ftype=s.ftype)
		self.sections = sections
		self._hasAnalyzedSections = False
		self._shouldImportMappings = machO.mappings.mutable


	def _analyzeSections(self, machO):
		# we need to make sure the section is not encrypted.
		self_sections = self.sections
		machO_encrypted = getattr(machO, 'encrypted', lambda x: False)
		machO_seek = machO.seek
		
		while not all(s.isAnalyzed for s in self_sections):
			for s in self_sections:
				if not s.isAnalyzed:
					offset = s.offset
					if s.isZeroFill or machO_encrypted(offset):
						s.isAnalyzed = True
					else:
						machO_seek(offset)
						s.isAnalyzed = not s.analyze(self, machO)
		
		self._hasAnalyzedSections = True
		

	def analyze(self, machO):
		# make sure all encryption_info commands are ready if they exist.
		if not all(lc.isAnalyzed for lc in machO.loadCommands.all('className', 'EncryptionInfoCommand')):
			return True
	
		# load sections if they aren't loaded yet.
		if not hasattr(self, 'sections'):
			self._loadSections(machO)

		# import mappings from sections if not closed yet
		if self._shouldImportMappings:
			addMapping = machO.mappings.add
			for s in self.sections:
				if s.isZeroFill:
					addMapping(Mapping(s.addr, s.size, s.offset, self.maxprot, self.initprot))
			machO.mappings.optimize()
			self._shouldImportMappings = False
	
		# make sure all segments are ready
		allSegments = machO.loadCommands.all('className', type(self).__name__)
		if not all(hasattr(seg, 'vmaddr') for seg in allSegments):
			return True
		
		# now analyze the sections.
		if not self._hasAnalyzedSections:
			self._analyzeSections(machO)
				
	
	def __str__(self):
		return "<Segment: {} [{}]>".format(self.segname, ', '.join(map(str, self._sections.values())))


	

LoadCommand.registerFactory(LC_SEGMENT, SegmentCommand)
LoadCommand.registerFactory(LC_SEGMENT_64, SegmentCommand)


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

		
	def allSections(self, idtype, sectid):
		'''Returns an iterable of all :class:`~macho.sections.section.Section`\\s
		having the specified section identifier. One of the following
		combinations of *idtype* and *sectid* may be used:
		
		+-----------------+------------------------------------------------------+
		| *idtype*        | *sectid*                                             |
		+=================+======================================================+
		| ``'sectname'``  | Section name, e.g. ``'__cstring'``.                  |
		+-----------------+------------------------------------------------------+
		| ``'className'`` | Class name of the section, e.g.                      |
		|                 | ``'CStringSection'``.                                |
		+-----------------+------------------------------------------------------+
		| ``'ftype'``     | Numerical value for the section type, e.g.           |
		|                 | :const:`~macho.sections.section.S_CSTRING_LITERALS`. |
		+-----------------+------------------------------------------------------+
		'''
		
		for seg in self.loadCommands.all('className', 'SegmentCommand'):
			for sect in seg.sections.all(idtype, sectid):
				yield sect

	def anySection(self, idtype, sectid):
		'''Get any :class:`~macho.sections.section.Section` having the specified
		section identifier. Returns ``None`` if no such section exists.'''
		for sect in self.allSections(idtype, sectid):
			return sect
		return None
	
	def anySectionProperty(self, idtype, sectid, prop, default=None):
		"""Retrieve a the section, and returns its property *prop* if exists. 
		
		Returns an *default* if the section does not exist. Returns ``None`` if
		the section is not analyzed.
		"""
		s = self.anySection(idtype, sectid)
		if not s:
			return default
		elif not s.isAnalyzed:
			return None
		else:
			return getattr(s, prop)
