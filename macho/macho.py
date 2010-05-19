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
from macho.utilities import readStruct, readFormatStruct
import os

class MachOError(Exception):
	def __init__(self, msg):
		self.message = msg
	def __str__(self):
		return self.message

class LoadCommand(object):
	"""An abstract load command."""
	
	__commandFactories = {}
	
	def registerFactory(lcs, cls):
		"""Register load commands with a class. For internal use only."""
		for lc in lcs:
			LoadCommand.__commandFactories[lc] = cls
	
	def create(machO, cmd, size, offset):
		"""Factory of a load command."""
		cls = LoadCommand.__commandFactories.get(cmd, LoadCommand)
		return cls(machO, cmd, size, offset)
	
	def seek(self):
		"""Move the file pointer to the offset of this load command."""
		self.o.file.seek(self.offset)
	
	def analyze(self):
		"""Analyze the load command."""
		pass
	
	def __init__(self, machO, cmd, size, offset):
		self.o = machO
		self.cmd = cmd
		self.size = size
		self.offset = offset


	def __str__(self):
		return "<LoadCommand: #{:x}/{:x}>".format(self.cmd, self.offset)

class MachO(object):
	"""A simple Mach-O format parser."""
	
	
	def __enter__(self):
		self.open()
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		return self.close(exc_type, exc_value, traceback)

	def __init__(self, filename, arch="armv6", lenientArchMatching=False):
		self.filename = filename
		self.arch = Arch(arch)
		self.lenientArchMatching = lenientArchMatching
		
		self.file = None
		
		self.loadCommands = []
		self.is64bit = False
		self.endian = '<'

		
	
	def open(self):
		"""Open the Mach-O file object for access.
		
		The 'with' statement should be used instead."""
		
		if self.file is None:
			self.file = open(self.filename, 'rb').__enter__()
		else:
			self.file.seek(0)
		self.__analyze()
	
	def close(self, exc_type=None, exc_value=None, traceback=None):
		"""Close the Mach-O file object.
		
		The 'with' statement should be used instead."""
	
		if self.file is not None:
			retval = self.file.__exit__(exc_type, exc_value, traceback)
			self.file = None
			return retval

		
	def __analyze(self):
		self.__pickArchFromFatFile()
		self.__readHeader()
		
		
	def __pickArchFromFatFile(self):
		(magic, nfat_arch) = readStruct(self.file, '>2L')
		
		# Reset and return if not a fat file.
		if magic != 0xcafebabe:
			self.file.seek(0)
			return
		
		# Get all the possible fat archs.
		offsets = {}
		for i in range(nfat_arch):
			(cputype, cpusubtype, offset, _, _) = readStruct(self.file, '>5L')
			offsets[Arch((cputype, cpusubtype))] = offset
		
		# Find the best match.
		scoreLimit = 1000 if not self.lenientArchMatching else 2000
		bestMatch = self.arch.bestMatch(offsets.keys(), scoreLimit)
		
		# Cannot find best match, raise an error. 
		if bestMatch is None:
			raise MachOError('Cannot find an arch matching "{}". Available archs are: {}'.format(self.arch, ', '.join(map(str, offsets.keys())) ))
		
		# Jump to offset if best match is found.
		self.file.seek(offsets[bestMatch])
		
		
	def __readHeader(self):
		(magic, ) = readStruct(self.file, '<L')
		
		# Read the magic.
		if magic == 0xfeedface:
			self.endian = '<'
		elif magic == 0xcefaedfe:
			self.endian = '>'
		elif magic == 0xfeedfacf:
			self.endian = '<'
			self.is64bit = True
		elif magic == 0xcffaedfe:
			self.endian = '>'
			self.is64bit = True
		else:
			raise MachOError('Invalid magic "0x{:08x}".'.format(magic))
		
		# Read the header.
		(cputype, cpusubtype, _, ncmds, _, _) = readFormatStruct(self.file, '6L', self.endian)
		arch = Arch((cputype, cpusubtype))
		if self.is64bit:
			self.file.read(4)	# there is a reserved member in 64-bit ABI.
		
		# Make sure the CPU type matches.
		scoreLimit = 1000 if not self.lenientArchMatching else 2000
		if self.arch.match(arch) >= scoreLimit:
			raise MachOError('Cannot find an arch matching "{}". Available arch is: {}'.format(self.arch, arch))
		
		# Read all load commands.
		for i in range(ncmds):
			(cmd, cmdsize) = readFormatStruct(self.file, '2L', self.endian)
			offset = self.file.tell()
			self.loadCommands.append(LoadCommand.create(self, cmd, cmdsize, offset))
			self.file.seek(cmdsize - 8, os.SEEK_CUR)
		
		loadCommandClasses = {}
		for lc in self.loadCommands:
			if type(lc) in loadCommandClasses:
				loadCommandClasses[type(lc)].append(lc)
			else:
				loadCommandClasses[type(lc)] = [lc]
		
		# Analyze all load commands.
		for lc in self.loadCommands:
			lc.seek()
			lc.analyze()
		
		
		
		
		