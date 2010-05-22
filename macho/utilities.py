#	
#	utilities.py ... Utility functions for Mach-O parsing.
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

"""Define functions that could help Mach-O parsing."""

import struct

def readString(f, encoding='utf_8'):
	"""Read a null-terminated string."""
	
	res = bytearray()
	while True:
		c = f.read(1)
		if not c or c[0] == 0:
			break
		else:
			res.append(c[0])
	return res.decode(encoding)


def peekString(f, encoding='utf_8', position=None):
	"""Read a null-terminated string without moving the cursor."""
	
	pos = f.tell()
	if position is not None:
		f.seek(position)
	res = readString(f, encoding)
	f.seek(pos)
	return res


def readULeb128(f):
	"""Read an unsigned little-endian base-128 integer."""
	
	res = 0
	bit = 0
	
	while True:
		c = f.read(1)
		if not c:
			break
		s = c[0] & 0x7f
		res |= s << bit
		bit += 7
		if not (c[0] & 0x80):
			break
	
	return res


def readSLeb128(f):
	"""Read a signed little-endian base-128 integer."""
	
	res = 0
	bit = 0
	c = None
	
	while True:
		c = f.read(1)
		if not c:
			break
		s = c[0] & 0x7f
		res |= s << bit
		bit += 7
		if not (c[0] & 0x80):
			break
	if c[0] & 0x40:
		res |= (-1) << bit
	
	return res


def readStruct(f, fmt):
	"""Read a packed structure."""
	sz = struct.calcsize(fmt)
	bs = f.read(sz)
	return struct.unpack(fmt, bs)


def formatStruct(fmt, endian, is64bit):
	"""Format a Python struct type encoding. Use ^ to represent a pointer-sized value."""
	return endian + fmt.translate({94: 'Q' if is64bit else 'L'})


def readFormatStruct(f, fmt, endian='>', is64bit=False):
	"""Format a Python struct type encoding and read it."""
	return readStruct(f, formatStruct(fmt, endian, is64bit))


def fromStringz(s):
	"""Strip terminating zeros of a byte string and decode it into a string."""
	return s.rstrip(b'\0').decode()


if __name__ == '__main__':
	from tempfile import TemporaryFile
	
	with TemporaryFile() as f:
		f.write(b"hell\xc3\xb3\0world\0\xf4\xa5\x32\xb7\x53wtf")
		f.seek(0)
		assert peekString(f) == 'helló'
		assert readString(f) == 'helló'
		assert peekString(f) == 'world'
		assert readString(f) == 'world'
		assert peekString(f, 'iso_8859_1') == 'ô¥2·Swtf'
		pos = f.tell()
		assert readULeb128(f) == 0xc92f4
		f.seek(pos)
		assert readSLeb128(f) == 0xc92f4
		pos = f.tell()
		assert readULeb128(f) == 0x29b7
		f.seek(pos)
		assert readSLeb128(f) == -0x1649
		assert readString(f) == 'wtf'

