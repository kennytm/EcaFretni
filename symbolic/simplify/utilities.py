#	
#	utitlities.py ... Utilities for simplification.
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

def split(iterable, predicate, rests):
	"""Return the results in the iterable that satisfies the predicate. Throw
	those which do not into the 3rd parameter.
	
	"""
	for i in iterable:
		if predicate(i):
			yield i
		else:
			rests.append(i)
