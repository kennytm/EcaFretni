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
	
	'''

	def __init__(self, *columnNames):
		self._values = []
		self._columns = dict((n, {}) for n in columnNames)
	
	def __getitem__(self, i): return self._values[i]
	def __iter__(self): return iter(self._values)
	def __len__(self): return len(self._values)

	def append(self, value, **columns):
		'''Append a value to the end of the table, and associate it with some
		column names, e.g.::
		
			dt.append(red_triangle, sides=3, color="red")
			dt.append(green_triangle, sides=3, color="green")
			dt.append(blue_square, sides=4, color="blue")
		
		'''
		self._values.append(value)
		self_columns = self._columns
		
		for colName, key in columns.items():
			col = self_columns[colName]
			if key in col:
				col[key].append(value)
			else:
				col[key] = [value]
				
	def column(self, columnName):
		'''
		Return an iterable of key-value pairs provided by a column, e.g.::
		
			for sides, obj in dt.column('sides'):
			    print('Number of sides:', sides)
			    print('Associated object:', obj)
		
		'''
		for key, lst in self._columns[columnName].items():
			for value in lst:
				yield (key, value)
		
	@property
	def values(self):
		'''Return a list of values in this data table.'''
		return self._values
	
	@property
	def columnNames(self):
		'''Return an iterable of valid column names in this data table.'''
		return self._columns.keys()
	
	def all(self, columnName, key):
		'''Return a list of values with the given *key* in the specified column.'''
		col = self._columns[columnName]
		if key in col:
			return col[key]
		else:
			return []
	
	def any(self, columnName, key, default=None):
		'''Return any value with the given *key* in the specified column. If no
		such key exists, a *default* value will be returned.'''
		col = self._columns[columnName]
		lst = []
		if key in col:
			lst = col[key]
		if len(lst):
			return lst[0]
		else:
			return default
	
	
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
	
	assert set(dt.column('sides')) == set([(3, 'r3'), (3, 'g3'), (4, 'b4'), (5, 'r5'), (4, 'r4')])
	assert set(dt.column('color')) == set([('red', 'r3'), ('green', 'g3'), ('blue', 'b4'), ('red', 'r5'), ('red', 'r4')])
	
	assert set(dt.all('sides', 3)) == set(['r3', 'g3'])
	assert dt.all('sides', 5) == ['r5']
	assert dt.all('sides', 7) == []
	assert dt.any('sides', 4) in ['b4', 'r4']
	assert dt.any('sides', 5) == 'r5'
	assert dt.any('sides', 6) is None
	assert dt.any('sides', 8, default='x') == 'x'
	
