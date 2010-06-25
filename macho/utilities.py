# -*- coding: utf-8 -*-
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

'''

This module is a collection of utility functions that will help Mach-O parsing.
It should not be used outside of the :mod:`macho` package.

Members
-------

'''


from struct import Struct, unpack_from
import os
import array

def readString(f, encoding='utf_8', returnLength=False):
	"""Read a null-terminated string from an :class:`mmap.mmap` object.
	
	If the *returnLength* argument is set to ``True``, this function will return
	a tuple instead of just the string. The 1st element is the string read, and
	the 2nd element is the number of bytes read. It can be different from the 
	string's length due to encoding.
	
	"""
	
	(string, length) = peekString(f, encoding=encoding, returnLength=True)
	try:
		f.seek(length+1, os.SEEK_CUR)
	except ValueError:
		f.seek(0, os.SEEK_END)
	
	if returnLength:
		return (string, length)
	else:
		return string

# This function is *very hot*. What to do?
def peekString(f, encoding='utf_8', position=-1, returnLength=False):
	"""Read a null-terminated string from a :class:`mmap.mmap` object without
	moving the cursor. 
	
	If *position* is nonnegative, the function will read from that offset instead
	of the current cursor location.
	
	"""
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


def peekFixedLengthString(f, length, encoding='utf_8', position=-1):
	"""Read a fixed length string from an :class:`mmap.mmap` object without
	moving the cursor.
	
	"""
	
	if position < 0:
		position = f.tell()
	return f[position:position+length].decode(encoding, 'replace')


def readULeb128(f):
	"""Read an unsigned little-endian base-128 integer from an :class:`mmap.mmap`
	object."""
	
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
	"""Read a signed little-endian base-128 integer from an :class:`mmap.mmap`
	object."""
	
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
	"""Make a :class:`struct.Struct` object.
	
	The *endian* argument should be either ``'>'`` or ``'<'``, and *is64bit*
	should be a boolean.
	
	Besides the standard format characters in :mod:`struct`, this function also
	supports:
	
	* ``^`` --- a pointer-sized value. Translates to ``Q`` if *is64bit* is ``True``,
	  ``L`` otherwise.
	
	* ``~`` --- alignment padding on 64-bit platforms. Translates to ``4x`` (skip
	  4 bytes) if *is64bit* is ``True``, an empty string otherwise.
	
	Example:
	
	>>> makeStruct('2^', '<', False).unpack(b'\\x00\\x10\\x00\\x00\\x00\\x20\\x00\\x00')
	(1024, 2048)
	>>> makeStruct('2^', '<', True).unpack(b'\\x00\\x10\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x20\\x00\\x00\\x00\\x00\\x00\\x00')
	(1024, 2048)
	
	"""
	
	return Struct(decodeStructFormat(fmt, endian, is64bit))


def decodeStructFormat(fmt, endian, is64bit):
	"""Converts the nonstandard symbols ``'^'`` and ``'~'`` into standard struct
	format characters."""
	return endian + fmt.translate({94: 'Q', 0x7e: '4x'} if is64bit else {94: 'L', 0x7e: ''})


def peekStructs(f, stru, count, position=-1):
	"""Returns an iteratable which unpacks the subsequent bytes of the
	:class:`mmap.mmap` object *f* into *count* copies of structures, given by the
	:class:`struct.Struct` object *stru*.
		
	.. warning:: Do not evaluate the returned iterable more than once. Convert it
	             to a ``list`` if you need to do so.
	
	"""

	if position < 0:
		position = f.tell()
		
	end = min(position + stru.size * count, len(f))
	
	return (stru.unpack_from(f, offset=o) for o in range(position, end, stru.size))


def peekPrimitives(f, fmt, count, endian, is64bit, position=-1):
	"""Returns an iteratable which unpacks the subsequent bytes of the 
	:class:`mmap.mmap` object *f* into *count* copies of primitives, given by
	the format *fmt*. 
	
	.. note:: ``'~'`` is not a primitive.
	
	"""
	
	if position < 0:
		position = f.tell()
	
	newFmt = decodeStructFormat(str(count) + fmt, endian, is64bit)
	return unpack_from(newFmt, f, offset=position)


def peekStruct(f, stru, position=-1):
	"""Returns a structure unpacked by *stru*."""
	if position < 0:
		position = f.tell()
	return stru.unpack_from(f, position)


def readStruct(f, stru, position=-1):
	"""Returns a structure unpacked by *stru* and advance the cursor in *f*."""
	val = peekStruct(f, stru, position)
	f.seek(stru.size, os.SEEK_CUR)
	return val



def fromStringz(s):
	"""Strip terminating zeros of a byte string and decode it into a string.
	
	>>> fromStringz(b'__TEXT\\0\\0\\0\\0\\0\\0')
	'__TEXT'
	
	
	"""
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
		assert list(peekPrimitives(f, 'B', 3, endian='>', is64bit=False, position=4)) == [0xc3, 0xb3, 0]
		assert list(peekPrimitives(f, 'H', 2, endian='<', is64bit=False, position=4)) == [0xb3c3, 0x7700]
		f.close()
