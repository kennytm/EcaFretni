#	
#	hexdump.py ... Dump bytes.
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

This module can print a byte array as hex dump to the standard output. This is
useful for debugging a binary blob.

>>> hexdump(b"\\x12\\x34\\x56foobar\\xab\\xcd\\xef" * 3)
 0        12 34 56 66 6f 6f 62 61 72 ab cd ef 12 34 56 66        `4Vfoobar````4Vf
10        6f 6f 62 61 72 ab cd ef 12 34 56 66 6f 6f 62 61        oobar````4Vfooba
20        72 ab cd ef                                            r```

Members
=======

'''

def _dumpLine(lineList, index, maxIndexWidth, width, visualizer, skip=0):
	pl = ['{0:{1}x}'.format(index, maxIndexWidth), '   '*skip + ' '.join(map('{:02x}'.format, lineList)) + '   ' * (width - skip - len(lineList))]
	if visualizer is not None:
		pl.append(visualizer(lineList, skip))
	print ('        '.join(pl))
	


def hexdump(arr, width=16, location=0, visualizer='ascii'):
	'''
	
	Dump the byte array on screen.
	
	The *location* argument changes the starting address to print, for example::
	
		>>> hexdump(b'123456' * 3)
		 0        31 32 33 34 35 36 31 32 33 34 35 36 31 32 33 34        1234561234561234
		10        35 36                                                  56
		>>> hexdump(b'123456' * 3, location=0x20fc)
		20f0                                            31 32 33 34                    1234
		2100        35 36 31 32 33 34 35 36 31 32 33 34 35 36              56123456123456

	The *visualizer* argument defines which function should be applied to the
	bytes to generate rightmost column. Only the visualizer ``'ascii'`` is
	defined in this module.

	''' 
	
	arrLen = len(arr)
	
	maxIndex = location + arrLen
	maxIndex -= maxIndex % width
	maxIndexWidth = len(hex(maxIndex)) - 2
	
	visualizerFunc = __visualizers.get(visualizer, None)
	
	index = location % width
	if index:
		location -= index
		index = width-index
		_dumpLine(arr[:index], location, maxIndexWidth, width, visualizerFunc, skip=width-index)
		location += width
	
	while index < arrLen:
		_dumpLine(arr[index:index+width], location, maxIndexWidth, width, visualizerFunc)
		index += width
		location += width

def listVisualizers():
	"""Return an iterator of strings listing all available visualizers."""
	
	return __visualizers.keys()

def registerVisualizer(key, func):
	"""Register a visualizer for use in hexdump.
	
	A visualizer should accept 2 parameters
	
	1. an :class:`bytes` object to be dumped.
	2. an integer describing how many empty bytes should be padded.
	
	and returns a string. For instance, an ASCII-based visualizer may be
	implemented as::
	
		def myAsciiVisualizer(theBytes, skip):
		    return ' '*skip + theBytes.decode(encoding='ascii', errors='replace')
	 
	"""
	__visualizers[key] = func
	

if hasattr(bytes, 'maketrans'):	# hack to make Sphinx work.
	__asciiTranslator = bytes.maketrans(bytes(range(0,0x20)) + bytes(range(0x7f,0x100)), b'`' * (0x20 + 0x100 - 0x7f))

def _asciiVisualizer(lineList, skip):
	return ' '*skip + lineList.translate(__asciiTranslator).decode()

__visualizers = {'ascii': _asciiVisualizer}


if __name__ == '__main__':
	hexdump(b'1234567\x8901234\x567890ashkfshfj\xaawroq23irme0 \x038mr0werm09asdsf', location=100)


