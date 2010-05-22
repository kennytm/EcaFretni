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

from macho.loadcommands.loadcommand import LoadCommand

class DylibCommand(LoadCommand):
	"""The dylib load command."""

	def analyze(self, machO):
		(offset, self.timestamp, self.version, self.minVersion) = machO.readFormatStruct('4L')
		self.name = machO.peekString(position=offset + self._offset - 8)
			
	def __str__(self):
		return "<Dylib {!r}>".format(self.name)

for i in ['LOAD_DYLIB', 'ID_DYLIB', 'LOAD_WEAK_DYLIB', 'REEXPORT_DYLIB', 'LAZY_LOAD_DYLIB', 'LOAD_UPWARD_DYLIB']:
	LoadCommand.registerFactory(i, DylibCommand)
