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

from macho.loadCommands.loadCommand import LoadCommand
from macho.utilities import readFormatStruct, readString

class DylibCommand(LoadCommand):
	"""The dylib load command."""

	def analyze(self):
		(offset, self.timestamp, self.version, self.minVersion) = readFormatStruct(self.o.file, '4L', self.o.endian, self.o.is64bit)
		self.o.file.seek(offset + self.offset - 8)
		self.name = readString(self.o.file)
			
	def __str__(self):
		return "<Dylib {!r}>".format(self.name)


LoadCommand.registerFactory('LOAD_DYLIB', DylibCommand)
LoadCommand.registerFactory('ID_DYLIB', DylibCommand)
LoadCommand.registerFactory('LOAD_WEAK_DYLIB', DylibCommand)
LoadCommand.registerFactory('REEXPORT_DYLIB', DylibCommand)
LoadCommand.registerFactory('LAZY_LOAD_DYLIB', DylibCommand)

