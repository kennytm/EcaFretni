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

def _dumpLine(lineList, index, maxIndexWidth, width, visualizer, skip=0):
	pl = ['{0:{1}x}'.format(index, maxIndexWidth), '   '*skip + ' '.join(map('{:02x}'.format, lineList)) + '   ' * (width - skip - len(lineList))]
	if visualizer is not None:
		pl.append(visualizer(lineList, skip))
	print ('        '.join(pl))
	


def hexdump(arr, width=16, location=0, visualizer='ascii'):
	"""Dump the byte array as hexadecimal."""
	
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
	"""Return an iterator listing all available visualizers."""
	return __visualizers.keys()

def registerVisualizer(key, func):
	"""Register a visualizer for use in hexdump.
	
	A visualizer should accept 2 parameters:
	 - a bytes object to be dumped
	 - an int describing how many empty bytes should be padded.
	and return a str.
	
	"""
	__visualizers[key] = func
	

__asciiTranslator = bytes.maketrans(bytes(range(0,0x20)) + bytes(range(0x7f,0x100)), b'`' * (0x20 + 0x100 - 0x7f))
def _asciiVisualizer(lineList, skip):
	return ' '*skip + lineList.translate(__asciiTranslator).decode()

__visualizers = {'ascii': _asciiVisualizer}


if __name__ == '__main__':
	hexdump(b'1234567\x8901234\x567890ashkfshfj\xaawroq23irme0 \x038mr0werm09asdsf', location=100)


