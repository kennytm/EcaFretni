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

from struct import Struct
import os
import array

def readString(f, encoding='utf_8', returnLength=False):
	"""Read a null-terminated string."""
	
	(string, length) = peekString(f, encoding=encoding, returnLength=True)
	try:
		f.seek(length+1, os.SEEK_CUR)
	except ValueError:
		f.seek(0, os.SEEK_END)
	
	if returnLength:
		return (string, length)
	else:
		return string


def peekString(f, encoding='utf_8', position=-1, returnLength=False):
	"""Read a null-terminated string without moving the cursor."""
	
	if position < 0:
		position = f.tell()
	nextZero = f.find(b'\0', position)
	if nextZero < 0:
		nextZero = len(f)
	string = f[position:nextZero].decode(encoding, 'replace')
	
	if returnLength:
		return (string, nextZero - position)
	else:
		return string


def peekFixedLengthString(f, length, encoding='utf_8', offset=-1):
	"""Peek a fixed length string."""
	if offset < 0:
		offset = f.tell()
	return f[offset:offset+length].decode(encoding, 'replace')


def readULeb128(f):
	"""Read an unsigned little-endian base-128 integer."""
	
	res = 0
	bit = 0
	pos = f.tell()
	maxpos = len(f)
	
	while maxpos > pos:
		c = f[pos]
		pos += 1
		s = c & 0x7f
		res |= s << bit
		bit += 7
		if not (c & 0x80):
			break
	
	f.seek(pos)
	
	return res


def readSLeb128(f):
	"""Read a signed little-endian base-128 integer."""
	
	res = 0
	bit = 0
	c = 0
	pos = f.tell()
	maxpos = len(f)
	
	while maxpos > pos:
		c = f[pos]
		pos += 1
		s = c & 0x7f
		res |= s << bit
		bit += 7
		if not (c & 0x80):
			break
	if c & 0x40:
		res |= (-1) << bit
	
	f.seek(pos)
	
	return res


def makeStruct(fmt, endian, is64bit):
	"""Make a struct.Struct object.
	
	Use ^ to represent a pointer-sized value, and ~ for a 32-bit padding needed
	on 64-bit architecture.
	
	"""
	
	return Struct(endian + fmt.translate({94: 'Q', 0x7e: '4x'} if is64bit else {94: 'L', 0x7e: ''}))


def peekStructs(f, stru, count, offset=-1):
	"""Returns an iteratable which lists all packed structures."""

	if offset < 0:
		offset = f.tell()
		
	end = min(offset + stru.size * count, len(f))
	
	return (stru.unpack_from(f, o) for o in range(offset, end, stru.size))
	

def peekStruct(f, stru, offset=-1):
	"""Peek a packed structure."""
	if offset < 0:
		offset = f.tell()
	return stru.unpack_from(f, offset)


def readStruct(f, stru, offset=-1):
	"""Read a packed structure."""
	val = peekStruct(f, stru, offset)
	f.seek(stru.size, os.SEEK_CUR)
	return val



def fromStringz(s):
	"""Strip terminating zeros of a byte string and decode it into a string."""
	return s.rstrip(b'\0').decode('ascii', 'replace')



if __name__ == '__main__':
	from tempfile import TemporaryFile
	from mmap import mmap
	
	with TemporaryFile() as g:
		g.write(b"hell\xc3\xb3\0world\0\xf4\xa5\x32\xb7\x53wtf")
		g.seek(0)
		f = mmap(g.fileno(), 0)
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
		f.close()
