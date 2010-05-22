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
	"""This error is raised when an arch is invalid (e.g. 'x96_64')."""

	def __init__(self, arch):
		self.arch = arch
	def __str__(self):
		return repr(self.arch)


class Arch(object):
	"""Represents a CPU architecture."""

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
	
	__revArchs = {y:x for x,y in __archs.items()}
	
	__archPairRx = re.compile(r"(\d+)\D*(\d+)")
	
	
	
	def __init__(self, arch):
		self.capability = 0
		if isinstance(arch, tuple):
			(self.cputype, self.cpusubtype, self.capability) = (arch[0], arch[1] & 0xFFFFFF, arch[1] >> 24)
		elif isinstance(arch, Arch):
			(self.cputype, self.cpusubtype, self.capability) = (arch.cputype, arch.cpusubtype, arch.capability)
		elif arch in self.__archs:
			(self.cputype, self.cpusubtype) = self.__archs[arch]
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
		"""Create a copy of the Arch."""
		return Arch(self)
	
	
	@property
	def is64bit(self):
		"""Checks if the architecture is 64-bit."""
		return bool(self.cputype & 0x1000000)
	
	
	def match(self, other):
		"""Compute the "match score" between two Archs. The score is defined as:
		
			          0: Totally match
			          1: Matched against a generic subtype.
			1000 - 1999: Matched against a compatible subtype, lower is better.
			       2000: Matched against an incompatible subtype.
			       5000: Matched against a generic type.
			      10000: No match.
		"""
		
		if not isinstance(other, Arch):
			print (other)
			other = Arch(other)
		
		if self.cputype == other.cputype:
			if self.cpusubtype == other.cpusubtype:
				return 0
			elif other.cpusubtype <= 0:
				return 1
			elif self.cpusubtype > other.cpusubtype:
				return self.cpusubtype - other.cpusubtype + 1000
			else:
				return 2000
		elif other.cputype <= 0:
			return 5000
		else:
			return 10000
	
	def bestMatch(self, others, minLevel=10000):
		best = min(others, key=self.match)
		if self.match(best) >= minLevel:
			return None
		else:
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
	
	c = Arch("armv7")
	d = Arch("armv6")
	assert a.match(c) == 10000
	assert c.match(a) == 10000
	assert 1000 <= c.match("armv6") < 2000
	assert c.match("arm") == 1
	assert d.match(c) == 2000
	assert d.match("any") == 5000
	assert not c.is64bit
	assert not d.is64bit
	
	assert str(c.bestMatch([a, b, c, d])) == "armv7"
	assert str(c.bestMatch([a, b, d])) == "armv6"
	assert str(c.bestMatch([a, b, "any", "arm"])) == "arm"
	assert str(c.bestMatch([a, b, "any"])) == "any"
	assert c.bestMatch([a, b]) is None
	
	assert str(c.bestMatch([a, b, c, d], 1000)) == "armv7"
	assert c.bestMatch([a, b, d], 1000) is None
	assert str(c.bestMatch([a, b, "any", "arm"], 1000)) == "arm"
	assert c.bestMatch([a, b, "any"], 1000) is None

