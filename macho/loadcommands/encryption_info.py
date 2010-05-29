#	
#	encryption_info.py ... LC_ENCRYPTION_INFO load command.
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
from macho.macho import MachO

class EncryptionInfoCommand(LoadCommand):
	"""The encryption info load command."""

	def analyze(self, machO):
		(self.cryptoff, self.cryptsize, self.cryptid) = machO.readFormatStruct('3L')
			
	def __str__(self):
		return "<EncryptionInfo {}/{:x}>".format(self.cryptid, self.cryptoff)

	def encrypted(self, offset):
		"""Checks if the offset is encrypted."""
		return self.cryptid != 0 and self.cryptoff <= offset < self.cryptoff + self.cryptsize


LoadCommand.registerFactory('ENCRYPTION_INFO', EncryptionInfoCommand)
		
def _macho_encrypted(self, offset):
	"""Checks if the offset is encrypted."""
	encCmds = self.allLoadCommands('EncryptionInfoCommand')
	return any(lc.encrypted(offset) for lc in encCmds)

MachO.encrypted = _macho_encrypted

