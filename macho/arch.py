#	
#	arch.py ... CPU architecture.
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

import re


class InvalidArchError(Exception):
	"""This error is raised when an arch is invalid (e.g. ``'x96_64'``)."""

	def __init__(self, arch):
		self.arch = arch
	def __str__(self):
		return repr(self.arch)


class Arch(object):
	"""Represents a CPU architecture.
	
	An :class:`Arch` can be created by one of the following methods:
	
	* Pass the name of the architecture, e.g. ``Arch('armv7')``.
	* Pass the CPU type and subtype as a tuple, e.g. ``Arch((12, 9))``.
	* Pass the CPU type and subtype in a string, e.g. ``Arch('12,9')``.
	
	* Pass another :class:`Arch` to create a copy.
	
	An :exc:`InvalidArchError` will be raised if the argument is none of the 
	above.
	
	"""

	__archs = {
	  "any": ( -1, -1) ,
	  "little": ( -1, 0) ,
	  "big": ( -1, 1) ,
	  "ppc64": (18 | 0x1000000, 0) ,
	  "x86_64": ( 7 | 0x1000000, 3) ,
	  "ppc970-64": ( 18| 0x1000000, 100) ,
	  "ppc": ( 18, 0) ,
	  "i386": ( 7, 3) ,
	  "m68k": ( 6, 1) ,
	  "hppa": ( 11, 0) ,
	  "sparc": ( 14, 0) ,
	  "m88k": ( 13, 0) ,
	  "i860": ( 15, 0) ,
	  "veo": ( 255, 2) ,
	  "arm": ( 12, 0) ,
	  "ppc601": ( 18, 1) ,
	  "ppc603": ( 18, 3) ,
	  "ppc603e": ( 18, 4) ,
	  "ppc603ev": ( 18, 5) ,
	  "ppc604": ( 18, 6) ,
	  "ppc604e": ( 18, 7) ,
	  "ppc750": ( 18, 9) ,
	  "ppc7400": ( 18, 10) ,
	  "ppc7450": ( 18, 11) ,
	  "ppc970": ( 18, 100) ,
	  "i486": ( 7, 4) ,
	  "i486SX": ( 7, 4 + 128) ,
	  "pentium": ( 7, 5 + (0 << 4)) ,
	  "i586": ( 7, 5) ,
	  "pentpro": ( 7, 6 + (1 << 4)) ,
	  "i686": ( 7, 6 + (1 << 4)) ,
	  "pentIIm3": ( 7, 6 + (3 << 4)) ,
	  "pentIIm5": ( 7, 6 + (5 << 4)) ,
	  "pentium4": ( 7, 10 + (0 << 4)) ,
	  "m68030": ( 6, 3) ,
	  "m68040": ( 6, 2) ,
	  "hppa7100LC": ( 11, 1) ,
	  "veo1": ( 255, 1) ,
	  "veo2": ( 255, 2) ,
	  "veo3": ( 255, 3) ,
	  "veo4": ( 255, 4) ,
	  "armv4t": ( 12, 5),
	  "armv5": ( 12, 7),
	  "xscale": ( 12, 8),
	  "armv6": ( 12, 6) ,
	  "armv7": ( 12, 9)
	}
	
	__revArchs = dict((y,x) for x,y in __archs.items())
	
	__archPairRx = re.compile(r"(\d+)\D*(\d+)")
	
	
	
	def __init__(self, arch):
		self.capability = 0
		if isinstance(arch, tuple):
			(self.cputype, self.cpusubtype, self.capability) = (arch[0], arch[1] & 0xFFFFFF, arch[1] >> 24)
		elif isinstance(arch, Arch):
			(self.cputype, self.cpusubtype, self.capability) = (arch.cputype, arch.cpusubtype, arch.capability)
		elif arch in self.__archs:
			(self.cputype, self.cpusubtype) = self.__archs[arch]
			self.capability = 0
		else:
			m = self.__archPairRx.search(arch)
			if m is None:
				raise InvalidArchError(arch)
			else:
				(self.cputype, self.cpusubtype) = m.groups()

	
	
	def __str__(self):
		return self.__revArchs.get((self.cputype, self.cpusubtype), str((self.cputype, self.cpusubtype)))
	
	def __hash__(self):
		return hash((self.cputype, self.cpusubtype, self.capability))
	
	def copy(self):
		"""Create a copy of the :class:`Arch`."""
		return Arch(self)
	
	def __eq__(self, other):
		if not isinstance(other, Arch):
			other = Arch(other)
		return self.cputype == other.cputype and self.cpusubtype == other.cpusubtype and self.capability == other.capability
	
	@property
	def is64bit(self):
		"""Checks if the architecture is 64-bit."""
		return bool(self.cputype & 0x1000000)
	
	
	def match(self, other):
		"""Compute the "match score" with another :class:`Arch`. The lower the
		score, the better. The score is defined as:
		
		+--------------+--------------------------+----------------------------+
		| Score        | Example                  | Meaning                    |
		+==============+==========================+============================+
		| 0            | ``armv6`` runs ``armv6`` | Totally match              |
		+--------------+--------------------------+----------------------------+
		| 1 --         | ``arm`` runs ``armv6``   | Generic target sub-type    |
		| 0xffffff     |                          |                            |
		+--------------+--------------------------+----------------------------+
		| 0x1000000 -- | ``armv6`` runs ``arm``   | Generic source sub-type    |
		| 0x1ffffff    |                          |                            |
		+--------------+--------------------------+----------------------------+
		| 0x2000000 -- | ``armv6`` runs ``armv4t``| Compatible sub-type        |
		| 0x2ffffff    |                          |                            |
		+--------------+--------------------------+----------------------------+
		| 0x3000000    | ``any`` runs ``armv6``   | Generic target type        |
		|              |                          | with specific source type  |
		+--------------+--------------------------+----------------------------+
		| 0x3000001    | ``any`` runs ``any``     | Generic types              |
		+--------------+--------------------------+----------------------------+
		| 0x3000002    | ``big`` runs ``big``     | Restricted endians         |
		+--------------+--------------------------+----------------------------+
		| 0x3000003    | ``any`` runs ``big``     | Generic target type,       |
		|              |                          | restricted source endian   |
		+--------------+--------------------------+----------------------------+
		| 0x3000004    | ``armv6`` runs ``any``   | Generic source type        |
		+--------------+--------------------------+----------------------------+
		| 0x3000005    | ``big`` runs ``any``     | Generic source type,       |
		|              |                          | restricted target endian   |
		+--------------+--------------------------+----------------------------+
		| 0x4000000 -- | ``armv6`` runs ``armv7`` | Incompatible sub-type      |
		| 0x4ffffff    |                          |                            |
		+--------------+--------------------------+----------------------------+
		| 0x5000001    | ``armv6`` runs ``big``   | Generic source type,       |
		|              |                          | restricted endian          |
		+--------------+--------------------------+----------------------------+
		| 0x5000002    | ``big`` runs ``armv6``   | Restricted target endian,  |
		|              |                          | specific source type       |
		+--------------+--------------------------+----------------------------+
		| 0xFFFFFFFF   | ``armv6`` runs ``i386``  | Does not match             |
		+--------------+--------------------------+----------------------------+
												
		This should be used such that, *self* is the user requested arch, and
		*other* the binary is compiled to. In the other words, we want to run an
		app compiled to *other* arch, on a CPU with the *self* arch.
		"""
		
		# score = areaOf(self - other) + big_value * areaOf(1 - self * other)
		
		if not isinstance(other, Arch):
			other = Arch(other)
		
		if self.cputype >= 0 and other.cputype >= 0:
			if self.cputype != other.cputype:
				return 0xffffffff
			elif self.cpusubtype == other.cpusubtype:	# armv6 runs armv6
				return 0
			elif self.cpusubtype <= 0:					# arm runs armv6
				return 0x1000000 - other.cpusubtype
			elif other.cpusubtype <= 0:					# armv6 runs arm
				return 0x1000000 + self.cpusubtype
			elif self.cpusubtype > other.cpusubtype:	# armv6 runs armv4t
				return 0x2000000 + self.cpusubtype - other.cpusubtype
			else:										# armv6 runs armv7
				return 0x4000000 + other.cpusubtype - self.cpusubtype
		
		elif self.cputype < 0:
			if self.cpusubtype not in (0, 1):
				if other.cputype >= 0:				# any runs armv6
					return 0x3000000
				elif other.cpusubtype in (0, 1):	# any runs big
					return 0x3000003
				else:								# any runs any
					return 0x3000001
			else:
				if other.cputype >= 0:					# big runs armv6 
					return 0x5000002
				if other.cpusubtype == self.cpusubtype:	# big runs big
					return 0x3000002
				elif other.cpusubtype in (0, 1):		# big runs little
					return 0xffffffff
				else:									# big runs any
					return 0x3000005
		
		elif other.cputype < 0:
			if other.cpusubtype in (0, 1):	# armv6 runs big
				return 0x5000001
			else:							# armv6 runs any
				return 0x3000004
		
	def bestMatch(self, others, minLevel=0xffffffff):
		'''Find the best match among a list of other architectures.
		
		>>> Arch('armv7').bestMatch(['i386', 'x86_64', 'ppc64', 'armv6'])
		'armv6'
		
		The argument *others* should be an iterable of objects that are
		convertible to :class:`Arch`.
		
		.. note::
		
			The compatible subtype order defined by Apple for ARM architecture is
		
			5. 'armv4t'
			6. 'armv6'
			7. 'armv5'
			8. 'xscale'
			
			9. 'armv7'
		
			This may cause confusion when comparing the match score among them,
			e.g. 
			
			>>> Arch('armv5').bestMatch(['armv6', 'armv7'])
			'armv7'

		'''
		self_match = self.match
		bestScore = minLevel
		best = None
		for other in others:
			score = self_match(other)
			if score < bestScore:
				bestScore = score
				best = other
		return best
			
			
if __name__ == "__main__":
	a = Arch("x86_64")
	assert a.cputype == 0x1000007 and a.cpusubtype == 3
	assert a.is64bit
	
	b = Arch((0x1000007, 3))
	assert str(b) == "x86_64"
	assert a.match(b) == 0
	assert b.match(a) == 0
	assert b.is64bit
	
	xarmv6 = Arch('armv6')
	xarm = Arch('arm')
	xany = Arch('any')
	xarmv4t = Arch('armv4t')
	xbig = Arch('big')
	assert xarmv6.match(xarmv6) == 0
	assert xarm.match(xarm) == 0
	assert 0 < xarm.match(xarmv6) < 0x1000000
	assert 0x1000000 <= xarmv6.match(xarm) < 0x2000000
	assert 0x2000000 <= xarmv6.match(xarmv4t) < 0x3000000
	assert xany.match(xarmv6) == 0x3000000
	assert xany.match(xarm) == 0x3000000
	assert xany.match(xany) == 0x3000001
	assert xbig.match(xbig) == 0x3000002
	assert xany.match(xbig) == 0x3000003
	assert xarmv6.match(xany) == 0x3000004
	assert xarm.match(xany) == 0x3000004
	assert xbig.match(xany) == 0x3000005
	assert 0x4000000 <= xarmv6.match('armv7') < 0x5000000
	assert xarmv6.match(xbig) == 0x5000001
	assert xbig.match(xarmv6) == 0x5000002
	assert xarmv6.match('i386') == 0xffffffff
	
	assert xarmv6.bestMatch(['i386', 'x86_64', 'ppc7400']) is None
	assert xarmv6.bestMatch(['i386', 'armv6', 'ppc7400']) == xarmv6
	assert xany.bestMatch(['i386', 'armv6', 'x86_64']) is not None
	assert Arch('armv7').bestMatch(['i386', 'armv6', 'x86_64']) == xarmv6
	assert xarmv6.bestMatch(['i386', 'armv7', 'x86_64']) == Arch('armv7')
	assert xarmv6.bestMatch(['i386', 'armv7', 'x86_64'], minLevel=0x4000000) is None
	
