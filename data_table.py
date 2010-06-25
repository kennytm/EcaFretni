#	
#	data_table.py ... Table-like container indiced by multiple keys.
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

from collections import Sequence, Sized

class DataTable(Sequence, Sized):
	'''
	This class is a sequence container which the items may be keyed by multiple
	"columns". This is similar to a table in a database::
	
		dt = DataTable('sides', 'color')
		dt.append(red_pentagon, sides=5, color='red')
		...
		for obj in dt.all('sides', 5):
		    print('Pentagon object:', obj)
	
	If the column names start with an exclamation mark, it is considered a
	column with unique items::
	
		dt = DataTable('!id', 'name')
		dt.append(johnDoe, id=112, name='John')	# Note that the column name does not have the '!'.
		dt.append(johnSmith, id=113, name='John')
		dt.append(janeError, id=112, name='Jane')	# this overrides johnDoe when accessing id.
		print(dt.all('id', 112))	# will only print [janeError].
	
	'''

	def __init__(self, *columnNames):
		self._values = []
		columns = {}
		for n in columnNames:
			if n[0] == '!':
				columns[n[1:]] = (True, {})
			else:
				columns[n] = (False, {})
		self._columns = columns
	
	def __getitem__(self, i): return self._values[i]
	def __iter__(self): return iter(self._values)
	def __len__(self): return len(self._values)

	def append(self, value, **columns):
		'''Append a *value* to the end of the table, and associate it with some
		column names, e.g.::
		
			dt.append(red_triangle, sides=3, color="red")
			dt.append(green_triangle, sides=3, color="green")
			dt.append(blue_square, sides=4, color="blue")

		'''
		list_append = list.append
		
		list_append(self._values, value)
		self_columns = self._columns
		
		for colName, key in columns.items():
			(isUnique, col) = self_columns[colName]
			if isUnique:
				col[key] = value
			elif key in col:
				list_append(col[key], value)
			else:
				col[key] = [value]
	
#	def removeMany(self, values):
#		'''Remove a large set (preferred) or sequence of *values* from the data
#		table.
#		
#		Note that this is a slow method (O(N)) if the data table is large.
#		'''
#		if not values:
#			return
#		self._values = [v for v in self._values if v not in values]
#		for keys in self._columns.values():
#			for key in keys.keys():
#				keys[key] = [v for v in keys[key] if v not in values]
	
	def column(self, columnName):
		'''
		Return an iterable of key-value pairs provided by a column, e.g.::
		
			for sides, obj in dt.column('sides'):
			    print('Number of sides:', sides)
			    print('Associated object:', obj)
		
		'''
		(isUnique, col) = self._columns[columnName]
		
		if isUnique:
			return col.items()
		else:
			return ((key, value) for key, lst in col.items() for value in lst)
		
				
	@property
	def values(self):
		'''Return a list of values in this data table.'''
		return self._values
	
	@property
	def columnNames(self):
		'''Return an iterable of valid column names in this data table.'''
		return self._columns.keys()
	
	def all(self, columnName, key):
		'''Return a list of values with the given *key* in the specified column,
		in insertion order.'''
		
		(isUnique, col) = self._columns[columnName]
		if key in col:
			res = col[key]
			if isUnique:
				res = [res]
			return res
		else:
			return []
	
	def any(self, columnName, key, default=None):
		'''Return any value with the given *key* in the specified column. If no
		such key exists, a *default* value will be returned.'''
		
		(isUnique, col) = self._columns[columnName]
		if key in col:
			lst = col[key]
			return lst if isUnique else lst[0]
		else:
			return default
	
	def any1(self, columnName, key):
		'''Return any value with the given *key* in the specified column. If no
		such key exists, a :exc:`KeyError` will be raised.
		
		This should be more efficient than :meth:`any` as there are less error
		checking.
		'''
		
		(isUnique, col) = self._columns[columnName]
		res = col[key]
		return res if isUnique else res[0]


	def isColumnUnique(self, columnName):
		'''Checks if a column is unique.
		
		.. note::
		
			Whether a column is unique or not is transparent to the user if used
			correctly. You should not change the code behavior based on this
			return value.
			
		'''
		return self._columns[columnName][0]

	def setColumnUnique(self, columnName, isUnique):
		'''Modify whether a column is unique. If you convert a non-unique column
		to unique, some data may not be referable from that column.
		'''
		
		res = self._columns[columnName]
		if res[0] != isUnique:
			res[0] = isUnique
			if isUnique:
				res[1] = dict((key, value[0]) for key, value in res[1].items())
			else:
				res[1] = dict((key, [value]) for key, value in res[1].items())
		

	def addColumn(self, columnName, keyGenerator, isUnique=False):
		'''Add or replace a column in the table, and generate keys using the
		function *keyGenerator*, for example::
		
			dt.addColumn('extangle', lambda shape: 360/shape.sides)
			dt.all('extangle', 120)	# returns all triangles.
		
		The *keyGenerator* should accept a value, and returns the corresponding
		key of that value. It should return ``None`` if the corresponding key
		does not exist.
		'''
		
		col = {}
		
		for val in self._values:
			key = keyGenerator(val)
			if key is not None:
				if isUnique:
					col[key] = val
				elif key in col:
					col[key].append(val)
				else:
					col[key] = [val]
		
		self._columns[columnName] = (isUnique, col)


	def removeColumn(self, columnName):
		'''Remove a column from the table.'''
		del self._columns[columnName]

	
	def contains(self, columnName, key):
		'''Checks if *key* exists in *columnName*.'''
		return key in self._columns[columnName][1]
	
	
if __name__ == '__main__':
	dt = DataTable('sides', 'color')
	dt.append('r3', sides=3, color='red')
	dt.append('g3', sides=3, color='green')
	dt.append('b4', sides=4, color='blue')
	dt.append('r5', sides=5, color='red')
	dt.append('r4', sides=4, color='red')
	
	assert dt.values == ['r3', 'g3', 'b4', 'r5', 'r4']
	assert set(dt.columnNames) == set(['sides', 'color'])
	assert len(dt) == 5
	assert list(dt) == ['r3', 'g3', 'b4', 'r5', 'r4']
	assert dt[3] == 'r5'
	assert 'b4' in dt
	assert 'r3' in dt
	assert 'r7' not in dt
	
	assert set(dt.column('sides')) == set([(3, 'r3'), (3, 'g3'), (4, 'b4'), (5, 'r5'), (4, 'r4')])
	assert set(dt.column('color')) == set([('red', 'r3'), ('green', 'g3'), ('blue', 'b4'), ('red', 'r5'), ('red', 'r4')])
	
	assert set(dt.all('sides', 3)) == set(['r3', 'g3'])
	assert dt.all('sides', 5) == ['r5']
	assert dt.all('sides', 7) == []
	assert dt.any('sides', 4) in ['b4', 'r4']
	assert dt.any('sides', 5) == 'r5'
	assert dt.any('sides', 6) is None
	assert dt.any('sides', 8, default='x') == 'x'
	
	assert dt.any1('sides', 5) == 'r5'
	errorRaised = False
	try:
		dt.any1('sides', 6)
	except KeyError:
		errorRaised = True
	assert errorRaised
	
	
#	dt.removeMany(['r3', 'r5', 'r7'])
#	
#	assert dt.values == ['g3', 'b4', 'r4']
#	assert set(dt.columnNames) == set(['sides', 'color'])
#	assert len(dt) == 3
#	assert list(dt) == ['g3', 'b4', 'r4']
#	assert dt[2] == 'r4'
#	assert 'b4' in dt
#	assert 'r3' not in dt
#	assert 'r7' not in dt
#	
#	assert set(dt.column('sides')) == set([(3, 'g3'), (4, 'b4'), (4, 'r4')])
#	assert set(dt.column('color')) == set([('green', 'g3'), ('blue', 'b4'), ('red', 'r4')])
#	
#	assert dt.all('sides', 3) == ['g3']
#	assert dt.all('sides', 5) == []
#	assert dt.all('sides', 7) == []
#	assert dt.any('sides', 4) in ['b4', 'r4']
#	assert dt.any('sides', 5) is None
#	assert dt.any('sides', 6) is None
#	assert dt.any('sides', 8, default='x') == 'x'

	dt2 = DataTable('!id', 'name')
	dt2.append('John Doe', id=1, name='John')
	dt2.append('John Smith', id=2, name='John')
	dt2.append('Jane Doe', id=3, name='Jane')
	
	assert len(dt2) == 3
	assert list(dt2) == ['John Doe', 'John Smith', 'Jane Doe']
	assert dt2.isColumnUnique('id')
	assert not dt2.isColumnUnique('name')
	assert set(dt2.columnNames) == set(['id', 'name'])
	assert dt2.all('id', 1) == ['John Doe']
	assert dt2.any('id', 3) == 'Jane Doe'
	assert dt2.all('name', 'John') == ['John Doe', 'John Smith']
	assert dt2.any('id', 4) is None
	assert dt2.any1('id', 1) == 'John Doe'
	errorRaised = False
	try:
		dt2.any1('id', 4)
	except KeyError:
		errorRaised = True
	assert errorRaised
	
	dt2.addColumn('surname', lambda s:s[5:])
	assert set(dt2.columnNames) == set(['id', 'name', 'surname'])
	assert dt2.all('surname', 'Doe') == ['John Doe', 'Jane Doe']
	assert dt2.any1('surname', 'Smith') == 'John Smith'
	assert dt2.any('surname', 'Peterson') is None
	assert len(dt2) == 3
	
	dt2.removeColumn('id')
	assert set(dt2.columnNames) == set(['surname', 'name'])
	assert len(dt2) == 3
