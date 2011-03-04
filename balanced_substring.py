#
#	balanced_substring.py ... Parse a balanced substring
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

import re



def balancedSubstring(string, index=0):
	'''
	Skip a balanced substring from specified index, and return the next string
	index.
	
	This function implements a simplistic stack-based parenthesis parser. It can
	consume a substring forming one balanced group of parenthesis, or a quoted
	string

	>>> '(foo)bar'[:balancedSubstring('(foo)bar')]
	'(foo)'
	>>> 'foo(bar)'[:balancedSubstring('foo(bar)')]
	'f'
	>>> '"foo"bar'[:balancedSubstring('"foo"bar')]
	'"foo"'

	A balanced substring means one of these:

	* a character
	* a string enclosed between a matching pair of parenthesis: ``(...)``,
	  ``[...]`` and ``{...}``
	* a quoted string: ``"..."``, ``'...'``, which can recognize the C-style
	  escape character e.g. ``'o\\'clock'``.

	.. note::

		This module is not designed for validation. The 3 different kinds of 
		parenthesis are not distinguished. That means ``"[foo)"`` will be
		considered as balanced.
		
	The optional parameter *index* can be used to tokenize the string::
	
		>>> balancedSubstring('(a)(bbb)c')
		3
		>>> balancedSubstring('(a)(bbb)c', index=3)
		8
	
	A number larger than the length of *string* will be returned on unbalanced
	paranthesis.
		
	'''
	
	level = 0
	quote_mode = ''
	strlen = len(string)
	while strlen > index:
		c = string[index]
		if c == '\\' and quote_mode:
			index += 1
		elif c == quote_mode:
			quote_mode = ''
			if level <= 0:
				break
			
		elif not quote_mode:
			if c in "([{":
				level += 1
			elif c in ")]}":
				level -= 1
			elif c in "\"'":
				quote_mode = c
		
			if level <= 0 and not quote_mode:
				break

		index += 1
		
	return index+1


_numberRe = re.compile('\d+')

def numericSubstring(string, index=0):
    '''
    Skip a numeric substring from specified index, return that number and the
    next string index.
    
    >>> numericSubstring('127foo')
    (127, 3)
    >>> numericSubstring('abc765def490', index=3)
    (765, 6)
    
    It is expected that ``string[index]`` is a digit. If not, an exception may
    be raised.
    '''
    
    m = _numberRe.match(string, index)
    return (int(m.group()), m.end())



if __name__ == '__main__':
	s = '(foo)bar[baz[bar]{bar}]'
	assert 5 == balancedSubstring(s)	# (foo)
	assert 6 == balancedSubstring(s, 5)	# b
	assert 7 == balancedSubstring(s, 6)	# a
	assert 8 == balancedSubstring(s, 7)	# r
	assert 23 == balancedSubstring(s, 8)	# [baz[bar]{bar}]
	
	s = '"foo\\"bar("\')b"az\''
	assert 11 == balancedSubstring(s)	# "foo\"bar("
	assert 18 == balancedSubstring(s,11) # ')b"az'
	
	s = '(((foo'
	assert balancedSubstring(s) > 6

	assert numericSubstring('127foo') == (127, 3)
	assert numericSubstring('abc765def490', index=3) == (765, 6)
