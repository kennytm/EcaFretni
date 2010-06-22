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

from macho.loadcommands.loadcommand import LoadCommand, LC_ENCRYPTION_INFO
from macho.macho import MachO
from monkey_patching import patch

class EncryptionInfoCommand(LoadCommand):
	"""The encryption info load command. This load command marks a range of file
	offset as encrypted. 
	
	An encrypted region cannot be used (the decryption procedure is in the
	kernel). Users may first check if a file offset is encrypted.
	
	.. attribute:: cryptoff
	
		The starting file offset of this encryption region.

	.. attribute:: cryptsize
	
		The size of this encryption region.
	
	.. attribute:: cryptid
	
		The method of encryption.
	
	"""

	def analyze(self, machO):
		(self.cryptoff, self.cryptsize, self.cryptid) = machO.readFormatStruct('3L')
			
	def __str__(self):
		return "<EncryptionInfo {}/{:x}>".format(self.cryptid, self.cryptoff)

	def encrypted(self, offset):
		"""Checks if the offset is encrypted."""
		return self.cryptid != 0 and self.cryptoff <= offset < self.cryptoff + self.cryptsize


LoadCommand.registerFactory(LC_ENCRYPTION_INFO, EncryptionInfoCommand)

@patch
class MachO_EncryptionPatches(MachO):
	"""This patch defines a single convenient function :meth:`encrypted` which
	can check if a file offset is encrypted."""

	def encrypted(self, fileoff):
		"""Checks if the file offset is in any encrypted region."""
		encCmds = self.loadCommands.all('className', 'EncryptionInfoCommand')
		return any(lc.encrypted(fileoff) for lc in encCmds)

