#
#	balancedSubstring.py ... Make a balanced substring
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

def balancedSubstring(string, index=0):
	level = 0
	quote_mode = ''
	while len(string) > index:
		c = string[index]
		if c == '\\' and quote_mode != '':
			index += 1
		elif c == quote_mode:
			quote_mode = ''
		elif quote_mode == '':
			if c in "([{":
				level += 1
			elif c in ")]}":
				level -= 1
			elif c in "\"'":
				quote_mode = c
		
			if level <= 0:
				break

		index += 1
	
	return index+1
