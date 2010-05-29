#	
#	_macho_utilities.py ... Adds methods from utitlities to MachO class.
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

"""WARNING: This package should never be imported. It is for use in macho.macho
only.

"""

import re
from macho.macho import MachO
from macho.utilities import *

def _seek(self, offset):
	"""Jump the cursor to the specific file offset, factoring out the file origin."""
	self._file.seek(offset + self._origin)

def _tell(self):
	"""Get the current file offset, factoring out the file origin."""
	return self._file.tell() - self._origin

def _getc(self):
	"""Read 1 byte from the file."""
	return self._file.read(1)[0]

def _readString(self, encoding='utf_8', returnLength=False):
	"""Read a null-terminated string."""
	return readString(self._file, encoding, returnLength)

def _peekString(self, encoding='utf_8', position=None):
	"""Read a null-terminated string without moving the cursor, factoring out the file origin."""
	if position is not None:
		position += self._origin
	return peekString(self._file, encoding, position)

def _readFormatStruct(self, fmt, endian=None, is64bit=None):
	"""Format a Python struct type encoding and read it.
	
	Always ignore the last 2 arguments unless you want to override the default in this call."""
	if endian is None:
		endian = self._endian
	if is64bit is None:
		is64bit = self._is64bit
	return readFormatStruct(self._file, fmt, endian, is64bit)

def _readULeb128(self):
	"""Read an unsigned little-endian base-128 integer."""
	return readULeb128(self._file)

def _readSLeb128(self):
	"""Read a signed little-endian base-128 integer."""
	return readSLeb128(self._file)

MachO.seek = _seek
MachO.tell = _tell
MachO.getc = _getc
MachO.readString = _readString
MachO.peekString = _peekString
MachO.readFormatStruct = _readFormatStruct
MachO.readULeb128 = _readULeb128
MachO.readSLeb128 = _readSLeb128

