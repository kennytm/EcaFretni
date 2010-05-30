#	
#	macho.py ... Mach-O format reader.
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

from macho.arch import Arch
from factory import factory
from macho.utilities import readStruct, readFormatStruct
from macho.loadcommands.loadcommand import LoadCommand
from mmap import mmap, ACCESS_READ
import os

class MachOError(Exception):
	def __init__(self, msg):
		self.message = msg
	def __str__(self):
		return self.message


class MachO(object):
	"""A simple Mach-O format parser."""
	
	
	def __enter__(self):
		self.open()
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		return self.close(exc_type, exc_value, traceback)

	def __init__(self, filename, arch="armv6", lenientArchMatching=False):
		self._filename = filename
		self._arch = Arch(arch)
		self._lenientArchMatching = lenientArchMatching
		
		self._fileno = -1
		self._file = None
		
		self._loadCommands = []
		self._is64bit = False
		self._endian = '<'

	
	@property
	def file(self):
		"""Return the file object of this Mach-O file."""
		return self._file
	
	@property
	def endian(self):
		"""Return the endianness of this Mach-O file."""
		return self._endian
	
	@property
	def is64bit(self):
		"""Return if this Mach-O file is using a 64-bit ABI."""
		return self._is64bit
	
	@property
	def pointerWidth(self):
		"""Return the width of pointer in the current ABI."""
		return 8 if self._is64bit else 4
	
	def open(self):
		"""Open the Mach-O file object for access.
		
		The 'with' statement should be used instead."""
		
		if self._file is None:
			flag = os.O_RDONLY | getattr(os, 'O_BINARY', 0)
			fileno = os.open(self._filename, flag)
			self._fileno = fileno
			self._file = mmap(fileno, 0, access=ACCESS_READ)
		else:
			self._file.seek(0)
		self.__analyze()
	
	def close(self, exc_type=None, exc_value=None, traceback=None):
		"""Close the Mach-O file object.
		
		The 'with' statement should be used instead."""
	
		if self._file is not None:
			self._file.close()
			self._file = None
		if self._fileno >= 0:
			os.close(self._fileno)
			self._fileno = -1


	def _allLoadCommands(self, cls):
		# get all load command which is not found in _loadCommandClasses.
		if isinstance(cls, int):
			cls = LoadCommand.cmdname(cls)
		if isinstance(cls, str):
			f = LoadCommand.getFactory(cls)
			# LoadCommand is returned only if the command is undefined.
			if f != LoadCommand:
				cls = f.__name__
			else:
				return []
		return self._loadCommandClasses.get(cls, [])
		

	def allLoadCommands(self, cls):
		"""Get all load command with the specified class."""
		if cls in self._loadCommandClasses:
			return self._loadCommandClasses[cls]
		else:
			return self._allLoadCommands(cls)
		
		
	
	def anyLoadCommand(self, cls):
		"""Get the first load command with the specified class."""
		arr = self.allLoadCommands(cls)
		if len(arr) > 0:
			return arr[0]
		else:
			return None

		
	def __analyze(self):
		self.__pickArchFromFatFile()
		self.__readMagic()
		self.__readHeader()
		self.__analyzeLoadCommands()
		
		
	def __pickArchFromFatFile(self):
		(magic, nfat_arch) = readStruct(self._file, '>2L')
		
		# Reset and return if not a fat file.
		if magic != 0xcafebabe:
			self._file.seek(0)
			return
		
		# Get all the possible fat archs.
		offsets = {}
		for i in range(nfat_arch):
			(cputype, cpusubtype, offset, _, _) = readStruct(self._file, '>5L')
			offsets[Arch((cputype, cpusubtype))] = offset
		
		# Find the best match.
		scoreLimit = 1000 if not self._lenientArchMatching else 2000
		bestMatch = self._arch.bestMatch(offsets.keys(), scoreLimit)
		
		# Cannot find best match, raise an error. 
		if bestMatch is None:
			raise MachOError('Cannot find an arch matching "{}". Available archs are: {}'.format(self._arch, ', '.join(map(str, offsets.keys())) ))
		
		# Jump to offset if best match is found.
		self._file.seek(offsets[bestMatch])
		
		
	def __readMagic(self):
		self._origin = self._file.tell()
		(magic, ) = readStruct(self._file, '<L')
		if magic == 0xfeedface:
			self._endian = '<'
		elif magic == 0xcefaedfe:
			self._endian = '>'
		elif magic == 0xfeedfacf:
			self._endian = '<'
			self._is64bit = True
		elif magic == 0xcffaedfe:
			self._endian = '>'
			self._is64bit = True
		else:
			raise MachOError('Invalid magic "0x{:08x}".'.format(magic))
	
	
	def __readHeader(self):
		# Read the header.
		(cputype, cpusubtype, _, ncmds, _, _) = readFormatStruct(self._file, '6L', self._endian)
		arch = Arch((cputype, cpusubtype))
		if self._is64bit:
			self._file.read(4)	# there is a reserved member in 64-bit ABI.
		
		# Make sure the CPU type matches.
		scoreLimit = 1000 if not self._lenientArchMatching else 2000
		if self._arch.match(arch) >= scoreLimit:
			raise MachOError('Cannot find an arch matching "{}". Available arch is: {}'.format(self._arch, arch))
		
		# Read all load commands.
		for i in range(ncmds):
			(cmd, cmdsize) = readFormatStruct(self._file, '2L', self._endian)
			offset = self.tell()
			cmdname = LoadCommand.cmdname(cmd)
			if cmdname is None:
				raise MachOError('Unrecognized load command 0x{:x}.'.format(cmd))
			self._loadCommands.append(LoadCommand.create(cmdname, cmdsize, offset))
			self._file.seek(cmdsize - 8, os.SEEK_CUR)
		
		
	def __analyzeLoadCommands(self):
		# Classify the load commands 
		loadCommandClasses = {}
		for lc in self._loadCommands:
			clsname = type(lc).__name__
			if clsname in loadCommandClasses:
				loadCommandClasses[clsname].append(lc)
			else:
				loadCommandClasses[clsname] = [lc]
		self._loadCommandClasses = loadCommandClasses
		
		# Analyze all load commands.
		requiresAnalysis = [True]*len(self._loadCommands)
		while any(requiresAnalysis):
			for i, lc in enumerate(self._loadCommands):
				if requiresAnalysis[i]:
					self.seek(lc.offset)
					requiresAnalysis[i] = lc.analyze(self)
		
import macho._macho_utilities
		
		
		