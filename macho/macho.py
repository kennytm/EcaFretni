#	
#	macho.py ... Mach-O file.
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

This module includes the :class:`MachO` class, representing a Mach-O file.

Example usage::

	with MachO('foo.dylib') as m:
	    print('Is 64-bit: ', m.is64bit)

Members
-------

'''

from .arch import Arch
from factory import factory
from .utilities import readStruct, makeStruct
from struct import Struct
from .loadcommands.loadcommand import LoadCommand
from mmap import mmap, ACCESS_READ
from data_table import DataTable
import os

class MachOError(Exception):
	"""An generic error thrown when the Mach-O file is invalid."""
	def __init__(self, msg):
		self.message = msg
	def __str__(self):
		return self.message


class MachO(object):
	'''The basic class that represents a Mach-O file.
	
	A normal Mach-O file consists of a header and many load commands. This class
	will only read the header and load all load commands into memory without
	further analysis. To allow analyze on a specific kind of load command, the
	corresponding module in :mod:`macho.loadcommands` should be imported.
	
	The optional *arch* argument is used if the Mach-O file is fat. The best
	architecture matching *arch* will be chosen on :meth:`open`.
	
	'''
	
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
		
		self._loadCommands = DataTable('className', 'cmd')
		self._is64bit = False
		self._endian = '<'
		
		self._structCache = {}
	
	@property
	def file(self):
		"""Return the :class:`mmap.mmap` object of this Mach-O file."""
		return self._file
	
	@property
	def endian(self):
		"""Return the endianness of this Mach-O file.
		
		+--------------+------------+
		| Return value | Endianness |
		+==============+============+
		| ``'>'``      | Big        |
		+--------------+------------+
		| ``'<'``      | Little     |
		+--------------+------------+
		
		"""
		return self._endian
	
	@property
	def is64bit(self):
		"""Return if this Mach-O file is using a 64-bit ABI."""
		return self._is64bit
	
	@property
	def pointerWidth(self):
		"""Return the width of pointer in the current ABI."""
		return 8 if self._is64bit else 4
	
	@property
	def origin(self):
		"""Return the origin of the current architecture.
		
		This is zero in normal Mach-O files. But in fat Mach-O files, which is
		composed of several normal Mach-O files and a fat header, the origin will
		be nonzero. When reading data given a file offset, the location will be
		shifted by this value.
		
		Use the :meth:`seek` and :meth:`tell` methods to transparently use a file
		offset without checking the :attr:`origin`.
		"""
		return self._origin
	
	def open(self):
		"""Open the Mach-O file object for access.
		
		.. note:: You should use the :keyword:`with` statement instead of calling
		          this method explicitly.
		
		"""
		
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
		
		.. note:: You should use the :keyword:`with` statement instead of calling
		          this method explicitly.
		
		"""
	
		if self._file is not None:
			self._file.close()
			self._file = None
		if self._fileno >= 0:
			os.close(self._fileno)
			self._fileno = -1

	@property
	def loadCommands(self):
		'''Get a (read-only) :class:`~data_table.DataTable` of
		:class:`~macho.loadcommand.LoadCommands`\\s, with the following column
		names: ``'className'`` and ``'cmd'``.
		
		The column ``'className'`` is the class name of the LoadCommand, e.g. 
		``'EncryptionInfoCommand'``.
		
		The column ``'cmd'`` is the command name, e.g. ``'ENCRYPTION_INFO'``.
		'''
		return self._loadCommands

	def seek(self, offset):
		"""Jump the cursor to the specific file offset, factoring out the
		:attr:`origin`."""
		self._file.seek(offset + self._origin)

	def tell(self):
		"""Get the current file offset, factoring out the :attr:`origin`."""
		return self._file.tell() - self._origin

	def makeStruct(self, fmt):
		"""Create a :class:`struct.Struct` object. See
		:func:`macho.utilities.makeStruct` for detail."""
		sc = self._structCache
		if fmt not in sc:
			sc[fmt] = makeStruct(fmt, endian=self._endian, is64bit=self._is64bit)
		return sc[fmt]
		
	def __analyze(self):
		self.__pickArchFromFatFile()
		self.__readMagic()
		self.__readHeader()
		self.__analyzeLoadCommands()
		
	def __pickArchFromFatFile(self):
		(magic, nfat_arch) = readStruct(self._file, Struct('>2L'))
		
		# Reset and return if not a fat file.
		if magic != 0xcafebabe:
			self._file.seek(0)
			return
		
		# Get all the possible fat archs.
		offsets = {}
		for i in range(nfat_arch):
			(cputype, cpusubtype, offset, _, _) = readStruct(self._file, Struct('>5L'))
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
		(magic, ) = readStruct(self._file, Struct('<L'))
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
		headerStruct = self.makeStruct('6L~')
		cmdStruct = self.makeStruct('2L')
		
		self_loadCommands_append = self._loadCommands.append
		self_file_seek = self._file.seek
		self_tell = self.tell
		LoadCommand_create = LoadCommand.create
		LoadCommand_cmdname = LoadCommand.cmdname
	
		# Read the header.
		(cputype, cpusubtype, _, ncmds, _, _) = readStruct(self._file, headerStruct)
		arch = Arch((cputype, cpusubtype))
		
		# Make sure the CPU type matches.
		scoreLimit = 1000 if not self._lenientArchMatching else 2000
		if self._arch.match(arch) >= scoreLimit:
			raise MachOError('Cannot find an arch matching "{}". Available arch is: {}'.format(self._arch, arch))
		
		# Read all load commands.
		for i in range(ncmds):
			(cmd, cmdsize) = readStruct(self._file, cmdStruct)
			offset = self_tell()
			cmdname = LoadCommand_cmdname(cmd)
			if cmdname is None:
				raise MachOError('Unrecognized load command 0x{:x}.'.format(cmd))
			lc = LoadCommand_create(cmdname, cmdsize, offset)
			self_loadCommands_append(lc, cmd=cmdname, className=type(lc).__name__)
			self_file_seek(cmdsize - 8, os.SEEK_CUR)
		
	def __analyzeLoadCommands(self):
		# Analyze all load commands.
		requiresAnalysis = [True]*len(self._loadCommands)
		while any(requiresAnalysis):
			for i, lc in enumerate(self._loadCommands):
				if requiresAnalysis[i]:
					self.seek(lc.offset)
					requiresAnalysis[i] = lc.analyze(self)
