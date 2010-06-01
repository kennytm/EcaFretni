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

'''

This module contains the function :func:`balancedSubstring`, which implements a 
simplistic stack-based parenthesis parser. It can consume a substring forming
one balanced group of parenthesis, or a quoted string

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


Members
=======
'''

class UnbalancedSubstringError(Exception):
	"""An error thrown when the string to parse is not balanced."""
	def __init__(self, level):
		self.level = level
	
	def __str__(self):
		return 'Unbalanced substring. Missing {} closing parenthesis.'.format(self.level)


def balancedSubstring(string, index=0, raiseOnUnbalanced=False):
	'''
	
	Skip a balanced substring from specified index, and return the next string
	index.
		
	The optional parameter *index* can be used to tokenize the string::
	
		>>> balancedSubstring('(a)(bbb)c')
		3
		>>> balancedSubstring('(a)(bbb)c', index=3)
		8
	
	If the *raiseOnUnbalanced* argument is set to ``True``, this function will
	raise an :exc:`UnbalancedSubstringError` on unbalanced paranthesis.
	Otherwise, a number larger than the length of *string* will be returned.
		
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
	
	if level > 0 and raiseOnUnbalanced:
		raise UnbalancedSubstringError(level)
	
	return index+1

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
	caughtException = False
	assert balancedSubstring(s) > 6
	try:
		balancedSubstring(s, raiseOnUnbalanced=True)
	except UnbalancedSubstringError as err:
		print("Caught expected exception:", err)
		caughtException = True
	
	assert caughtException
	

