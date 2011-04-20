#	
#	dylib.py ... LC_LOAD_DYLIB load command.
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

from macho.loadcommands.loadcommand import LoadCommand, LC_LOAD_DYLIB, LC_ID_DYLIB, LC_LOAD_WEAK_DYLIB, LC_REEXPORT_DYLIB, LC_LAZY_LOAD_DYLIB, LC_LOAD_UPWARD_DYLIB
from macho.utilities import peekString, peekStruct
from monkey_patching import patch
from macho.macho import MachO

class DylibCommand(LoadCommand):
	"""A dylib load command. This can represent any of these commands:
	
	.. hlist::
	
		* :const:`~macho.loadcommands.loadcommand.LC_LOAD_DYLIB` (``0x0c``)
		* :const:`~macho.loadcommands.loadcommand.LC_ID_DYLIB` (``0x0d``)
		* :const:`~macho.loadcommands.loadcommand.LC_LOAD_WEAK_DYLIB` (``0x18``)
		* :const:`~macho.loadcommands.loadcommand.LC_REEXPORT_DYLIB` (``0x1f``)
		* :const:`~macho.loadcommands.loadcommand.LC_LAZY_LOAD_DYLIB` (``0x20``)
		* :const:`~macho.loadcommands.loadcommand.LC_LOAD_UPWARD_DYLIB` (``0x23``)
	
	.. attribute:: name
	
		The name of the dynamic library.
	
	.. attribute:: timestamp
	
		The timestamp of the dynamic library.
	
	.. attribute:: version
	
		The version of the dynamic library.
	
	.. attribute:: minVersion
	
		The compatibility version of the dynamic library.
	
	"""

	def analyze(self, machO):
		(offset, self.timestamp, self.version, self.minVersion) = peekStruct(machO.file, machO.makeStruct('4L'))
		self.name = peekString(machO.file, position=offset + machO.origin + self.offset - 8)
			
	def __str__(self):
		return "<Dylib {!r}>".format(self.name)

for i in (LC_LOAD_DYLIB, LC_ID_DYLIB, LC_LOAD_WEAK_DYLIB, LC_REEXPORT_DYLIB, LC_LAZY_LOAD_DYLIB, LC_LOAD_UPWARD_DYLIB):
	LoadCommand.registerFactory(i, DylibCommand)

@patch
class MachO_FromLibord(MachO):
	"""This patch defines a single convenient function :meth:`dylibFromLibord`
	which can convert a library ordinal to a :class:`DylibCommand` object."""
	
	def dylibFromLibord(self, libord):
		"""Converts library ordinal to a :class:`DylibCommand` object. Returns
		``None`` if the input is invalid."""
		
		if libord < 0:
			return None
		
		lcs = self.loadCommands
		if not libord:
			return lcs.any1('cmd', LC_ID_DYLIB)
		
		else:
			for lc in lcs:
				if lc.cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB, LC_LOAD_UPWARD_DYLIB):
					libord -= 1
				if not libord:
					return lc
			return None


