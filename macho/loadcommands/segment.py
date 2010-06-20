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

'''

This module provides the :class:`SegmentCommand` representing the a segment load
command. A segment consists of many sections, which contain actual code and
data.

.. note::

	Sections falling in the encrypted region will not be analyzed. See
	:mod:`macho.loadcommands.encryption_info` for detail.

This module also provides virtual memory (VM) address-related methods to
:class:`macho.macho.MachO` as they are meaningful only to segments.

Patches
-------

.. method:: macho.macho.MachO.fromVM(vmaddr)

	Convert a VM address to file offset. Returns -1 if the address does not
	exist.

.. method:: macho.macho.MachO.toVM(fileoff)

	Convert a file offset to VM address. Returns -1 if the address does not
	exist.
	
.. method:: macho.macho.MachO.deref(vmaddr, stru)

	Dereference a structure at VM address *vmaddr*. The structure is defined by
	the :class:`struct.Struct` instance *stru*. Returns ``None`` if the address
	does not exist.

.. method:: macho.macho.MachO.derefString(vmaddr)

	Read a null-terminated string at VM address *vmaddr*. Returns ``None`` if
	the address does not exist.

.. attribute:: macho.macho.MachO.segments

	Get a dictionary of :class:`Segment`\\s keyed by segment name, for example
	
	>>> m.segments['__TEXT']

.. method:: macho.macho.MachO.allSections(idtype, sectid)

	Returns an iterable of all :class:`~macho.sections.section.Section`\\s
	having the specified section identifier.
	
	If *idtype* is ``'sectname'``, then the *sectid* should be a section name,
	e.g. ``'__cstring'``.
	
	If *idtype* is ``'className'``, then the *sectid* should be the class name 
	of the section to find, e.g. ``'CStringSection'``.

.. method:: macho.macho.MachO.anySection(idtype, sectid):

	Get any :class:`~macho.sections.section.Section` having the specified
	section identifier. Returns ``None`` if no such section exists.

Members
-------

'''

from macho.loadcommands.loadcommand import LoadCommand
from macho.utilities import fromStringz, peekStructs, peekString, readStruct, peekStruct
from macho.macho import MachO
from factory import factory
from macho.sections.section import Section
from data_table import DataTable
import struct

class SegmentCommand(LoadCommand):
	'''The segment load command. This can represent the 32-bit ``SEGMENT``
	command (``0x01``) or the 64-bit ``SEGMENT_64`` command  (``0x19``).
	
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


def _macho_forEachSegment(func):
	def f(self, vmaddr):
		allAddrs = (func(lc, vmaddr) for lc in self.loadCommands.all('className', 'SegmentCommand'))
		try:
			return next(addr for addr in allAddrs if addr >= 0)
		except StopIteration:
			return -1
	return f

def _macho_deref(self, vmaddr, stru):
	"""Dereference a struct at vmaddr."""
	allDerefs = (lc.deref(vmaddr, stru) for lc in self.loadCommands.all('className', 'SegmentCommand'))
	try:
		return next(val for val in allDerefs if val is not None)
	except StopIteration:
		return None

def _macho_segment(self, segname):
	"""Get the segment given its name"""
	try:
		return next(lc for lc in self.loadCommands.all('className', 'SegmentCommand') if lc.segname == segname)
	except StopIteration:
		return None

def _macho_derefString(self, vmaddr, encoding='utf_8', returnLength=False):
	"""Dereference a string."""
	offset = self.fromVM(vmaddr)
	if offset < 0:
		return None
	cur = self.tell()
	self.seek(offset)
	res = peekString(self.file, encoding=encoding, returnLength=returnLength)
	self.seek(cur)
	return res
	
def _macho_allSections(self, idtype, sectid):
	allSegs = self.loadCommands.all('className', 'SegmentCommand')
	for seg in allSegs:
		for sect in seg.sections.all(idtype, sectid):
			yield sect

def _macho_anySection(self, idtype, sectid):
	try:
		return next(self.allSections(idtype, sectid))
	except StopIteration:
		return None
		

MachO.fromVM = _macho_forEachSegment(SegmentCommand.fromVM)
MachO.toVM = _macho_forEachSegment(SegmentCommand.toVM)
MachO.deref = _macho_deref
MachO.derefString = _macho_derefString
MachO.segment = _macho_segment
MachO.allSections = _macho_allSections
MachO.anySection = _macho_anySection
