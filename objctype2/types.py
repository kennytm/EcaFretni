#
#    types.py ... Objective-C type system.
#    Copyright (C) 2011  KennyTM~ <kennytm@gmail.com>
#    
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import Hashable


class Type(Hashable):
    "The base class to represent Objective-C encodeable type."
        
    def encode(self):
        "Return the canonical encoding of this type."
        assert False

    def sizeof(self, is64bit=False):
        "Return the size occupied by this type."
        assert False
    
    def alignof(self, is64bit=False):
        "Return the alignment used by this type."
        assert False
        
    def __eq__(self, other):
        "Check if two types are equal."
        return NotImplemented
    
    def __hash__(self):
        "Compute the hash of this type (could be slow if the type is large)."
        assert False

#-------------------------------------------------------------------------------

CLASS='#'
NXATOM='%'
SEL=':'
BOOL_C99='B'
UNSIGNED_CHAR='C'
UNSIGNED_INT='I'
UNSIGNED_LONG='L'
UNSIGNED_LONG_LONG='Q'
UNSIGNED_SHORT='S'
BOOL='c'
CHAR='c'
DOUBLE='d'
FLOAT='f'
INT='i'
LONG='l'
LONG_LONG='q'
SHORT='s'
VOID='v'
FUNCTION_POINTER='^?'
BLOCK='@?'

_Primitive_sizeof_get = {
    BOOL_C99: 1,
    UNSIGNED_CHAR: 1,
    UNSIGNED_INT: 4,
    UNSIGNED_LONG: 4,
    UNSIGNED_LONG_LONG: 8,
    UNSIGNED_SHORT: 2,
    BOOL: 1,
    CHAR: 1,
    DOUBLE: 8,
    FLOAT: 4,
    INT: 4,
    LONG: 4,
    LONG_LONG: 8,
    SHORT: 2,
    VOID: 1,
}.get

class Primitive(Type):
    """
    Primitive types. These types are the most basic types in the Objective-C
    language.
    
    The supported *primitive*\s are:
    
    +-----------------------------+----------+------------------------+--------------------+
    | Constant                    | Encoding | Objective-C type       | Size and Alignment |
    +=============================+==========+========================+====================+
    | :const:`CHAR`,              | ``'c'``  | ``signed char``,       | 1                  |
    | :const:`BOOL`               |          | ``BOOL``               |                    |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`SHORT`              | ``'s'``  | ``signed short``       | 2                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`INT`                | ``'i'``  | ``signed int``         | 4                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`LONG`               | ``'l'``  | ``signed long``        | 4                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`LONG_LONG`          | ``'q'``  | ``signed long long``   | 8                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`UNSIGNED_CHAR`      | ``'C'``  | ``unsigned char``      | 1                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`UNSIGNED_SHORT`     | ``'S'``  | ``unsigned short``     | 2                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`UNSIGNED_INT`       | ``'I'``  | ``unsigned int``       | 4                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`UNSIGNED_LONG`      | ``'L'``  | ``unsigned long``      | 4                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`UNSIGNED_LONG_LONG` | ``'Q'``  | ``unsigned long long`` | 8                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`FLOAT`              | ``'f'``  | ``float``              | 4                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`DOUBLE`             | ``'d'``  | ``double``             | 8                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`VOID`               | ``'v'``  | ``void``               | 1                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`BOOL_C99`           | ``'B'``  | ``_Bool`` (C99)        | 1                  |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`CLASS`              | ``'#'``  | ``Class``              | pointer            |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`SEL`                | ``':'``  | ``SEL``                | pointer            |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`FUNCTION_POINTER`   | ``'^?'`` | ``T(*)(...)``          | pointer            |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`BLOCK`              | ``'@?'`` | ``T(^)(...)``          | pointer            |
    +-----------------------------+----------+------------------------+--------------------+
    | :const:`NXATOM`             | ``'%'``  | ``NXAtom``             | pointer            |
    +-----------------------------+----------+------------------------+--------------------+

    .. note:: The ``char*`` type (``'*'``) is *not* considered a primitive type 
        in this package. It should be converted to a :class:`Unary` type ``'^c'``.
        
    
    .. attribute:: primitive
    
        The type encoding representing which primitive type it is.
    
    """
    
    def __init__(self, primitive):
        self.primitive = primitive

    def __eq__(self, other):
        if isinstance(other, Primitive):
            return self.primitive == other.primitive
        else:
            return False

    def encode(self):
        return self.primitive
    
    def __repr__(self):
        return "Primitive({0!r})".format(self.primitive)
    
    def sizeof(self, is64bit=False):
        return _Primitive_sizeof_get(self.primitive, 8 if is64bit else 4)
    
    def alignof(self, is64bit=False):
        return self.sizeof(is64bit)
        
    def __hash__(self):
        return hash(self.primitive)
    
#-------------------------------------------------------------------------------

POINTER = '^'
COMPLEX = 'j'
ONEWAY = 'V'
CONST = 'r'
BYCOPY = 'O'
BYREF = 'R'
IN = 'n'
OUT = 'o'
INOUT = 'N'
GCINVISIBLE = '!'

class Unary(Type):
    """
    Unary types. These types consists of 2 elements: a type and a modifier. A
    unary type is said to be derived from the base type.
    
    The supported *modifier*\s are:
    
    +----------------------+----------+----------------------+---------------+-----------+
    | Constant             | Encoding | Objective-C type     | Size          | Alignment |
    +======================+==========+======================+===============+===========+
    | :const:`POINTER`     | ``'^'``  | ``T*``               | pointer       | pointer   |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`COMPLEX`     | ``'j'``  | ``_Complex T`` (C99) | 2 * base type | base type |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`ONEWAY`      | ``'V'``  | ``oneway T``         | base type     | base type |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`CONST`       | ``'r'``  | ``const T``          | base type     | base type |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`BYCOPY`      | ``'O'``  | ``bycopy T``         | base type     | base type |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`BYREF`       | ``'R'``  | ``byref T``          | base type     | base type |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`IN`          | ``'n'``  | ``in T``             | base type     | base type |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`OUT`         | ``'o'``  | ``out T``            | base type     | base type |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`INOUT`       | ``'N'``  | ``inout T``          | base type     | base type |
    +----------------------+----------+----------------------+---------------+-----------+
    | :const:`GCINVISIBLE` | ``'!'``  | N/A                  | base type     | base type |
    +----------------------+----------+----------------------+---------------+-----------+

    .. attribute:: modifier
    
        The type encoding representing which modifier it is.

    .. attribute:: baseType
    
        The base :class:`Type` of this unary type.

    """
    
    def __init__(self, modifier, baseType):
        self.modifier = modifier
        self.baseType = baseType
    
    def __eq__(self, other):
        if isinstance(other, Unary):
            return self.modifier == other.modifier and self.baseType == other.baseType
        else:
            return False

    def encode(self):
        return self.modifier + self.baseType.encode()
    
    def __repr__(self):
        return "Unary({0!r}, {1!r})".format(self.modifier, self.baseType)
    
    def sizeof(self, is64bit=False):
        m = self.modifier
        if m == '^':
            return 8 if is64bit else 4
        elif m == 'j':
            return 2 * self.baseType.sizeof(is64bit)
        else:
            return self.baseType.sizeof(is64bit)

    def alignof(self, is64bit=False):
        if self.modifier == '^':
            return 8 if is64bit else 4
        else:
            return self.baseType.alignof(is64bit)
            
    def __hash__(self):
        return hash((self.modifier, self.baseType))

#-------------------------------------------------------------------------------

class Bitfield(Type):
    """
    Bitfield type. A bitfield can only appear inside a :class:`Struct`.
    
    It is assumed the bitfield is based on the ``unsigned int`` type, so the
    :meth:`~Type.sizeof` and :meth:`~Type.alignof` are 4.
    
    .. attribute:: bits
        
        Number of bits this bitfield type holds.
    """
    
    def __init__(self, bits):
        self.bits = bits
    
    def __eq__(self, other):
        if isinstance(other, Bitfield):
            return self.bits == other.bits
        else:
            return False
    
    def encode(self):
        return 'b' + str(self.bits)
    
    def __repr__(self):
        return "Bitfield({0!r})".format(self.bits)
    
    def sizeof(self, is64bit=False):
        return 4
    
    def alignof(self, is64bit=False):
        return 4

    def __hash__(self):
        return hash(self.bits)

#-------------------------------------------------------------------------------

class Array(Type):
    """
    Fixed-length array type. An array is a contiguously allocated memory for a
    single base type.
    
    .. attribute:: length
    
        Length of the array. It could be zero.
    
    .. attribute:: baseType
    
        The base :class:`Type` of the array. 
        
    """
    
    def __init__(self, length, baseType):
        self.length = length
        self.baseType = baseType
    
    def __eq__(self, other):
        if isinstance(other, Array):
            return self.length == other.length and self.baseType == other.baseType
        else:
            return False
    
    def encode(self):
        return "[{0}{1}]".format(self.length, self.baseType.encode())
    
    def __repr__(self):
        return "Array({0!r}, {1!r})".format(self.length, self.baseType)

    def sizeof(self, is64bit=False):
        return self.baseType.sizeof(is64bit) * self.length
    
    def alignof(self, is64bit=False):
        return self.baseType.alignof(is64bit)

    def __hash__(self):
        return hash((self.length, self.baseType))

#-------------------------------------------------------------------------------

class ObjCType(Type):
    """
    An Objective-C type, i.e. types that are compatible with ``id``. 
    
    .. attribute:: name
    
        The type name. If it is ``None``, the type refers to the generic ``id``
        type.
    
    .. attribute:: protocols
    
        An immutable list (tuple) containing the name of all protocols this type
        should adopt to, in alphabetical order.
    
    """
    
    def __init__(self, name=None, protocols=None):
        self.name = name
        self.protocols = tuple(sorted(set(protocols or [])))
    
    def __eq__(self, other):
        if isinstance(other, ObjCType):
            return self.name == other.name and self.protocols == other.protocols
        else:
            return False
        
    def encode(self):
        if self.name is None:
            if not self.protocols:
                return '@'
            else:
                return '@"<{0}>"'.format(','.join(self.protocols))
        else:
            if not self.protocols:
                return '@"{0}"'.format(self.name)
            else:
                return '@"{0}<{1}>"'.format(self.name, ','.join(self.protocols))
    
    def __repr__(self):
        if self.name is None:
            if not self.protocols:
                return 'ObjCType()'
            else:
                return 'ObjCType(protocols={0!r})'.format(self.protocols)
        else:
            if not self.protocols:
                return 'ObjCType({0!r})'.format(self.name)
            else:
                return 'ObjCType({0!r}, {1!r})'.format(self.name, self.protocols)

    def sizeof(self, is64bit=False):
        return 8 if is64bit else 4
    
    def alignof(self, is64bit=False):
        return 8 if is64bit else 4

    def __hash__(self):
        return hash((self.name, self.protocols))


#-------------------------------------------------------------------------------

class Struct(Type):
    """
    A ``struct`` or ``union``. These type consists of an ordered list of
    inhomogeneous types.
    
    .. attribute:: isUnion
    
        Whether this type is a ``union`` or a ``struct``.
    
    .. attribute:: name
    
        The name of the structure. It is ``'?'`` if the structure is anonymous.
    
    .. attribute:: members
    
        An immutable list of struct :class:`~Struct.Member`\s.
            
    """
    
    class Member(Hashable):
        """
        Member of a :class:`Struct`. You should not construct this class
        directly.
        
        .. attribute:: baseType
        
            The :class:`Type` of this member.
        
        .. attribute:: name
        
            The name of this member. Could be ``None``.
                
        """
    
        def __init__(self, baseType, name):
            self.baseType = baseType
            self.name = name
        
        def __eq__(self, other):
            return self.name == other.name and self.baseType == other.baseType
        
        def encode(self):
            bte = self.baseType.encode()
            if self.name:
                return '"{0}"{1}'.format(self.name, bte)
            else:
                return bte
                
        def _repr(self):
            s = repr(self.baseType)
            if self.name:
                s += ', ' + repr(self.name)
            return s
        
        def __repr__(self):
            s = 'Struct.Member(' + repr(self.baseType)
            if self.name:
                s += ', ' + repr(self.name)
            return s + ')'
        
        def __hash__(self):
            return hash((self.name, self.baseType))
        
            
    def __init__(self, name='?', isUnion=False):
        self.isUnion = isUnion
        self.name = name
        self.members = []
    
    def append(self, baseType, name=None):
        """
        Append a member to the structure.
        
        An :exc:`AttributeError` will be raised when attempting to append to a
        frozen structure.
        
        Returns the instance itself, thus you could use it as fluent interface.
        
            stru = Struct('CGPoint').append(Primitive(FLOAT), 'x').append(Primitive(FLOAT), 'y').freeze()
        """
        
        newMember = self.Member(baseType, name)
        self.members.append(newMember)
        
        return self
    
    def freeze(self):
        """
        Finish appending, and thus avoid more members to be :meth:`append`\ed to
        this structure.
        
        Returns the instance itself.
        """
        self.members = tuple(self.members)
        return self
    
    def __eq__(self, other):
        if isinstance(other, Struct):
            return self.isUnion == other.isUnion and self.name == other.name and self.members == other.members
    
    def encode(self):
        if self.isUnion:
            openParen = '('
            closeParen = ')'
        else:
            openParen = '{'
            closeParen = '}'
        
        if self.members:
            return "{0}{1}={2}{3}".format(openParen, self.name, ''.join(m.encode() for m in self.members), closeParen)
        else:
            return openParen + self.name + closeParen
    
    def __repr__(self):
        a = ['Struct({0!r}, isUnion={1}'.format(self.name, self.isUnion)]
        a.extend(m._repr() for m in self.members)
        return ').append('.join(a) + ')'
    
    def alignof(self, is64bit=False):
        return max(m.baseType.alignof(is64bit) for m in self.members)
    
    def sizeof(self, is64bit=False):
        if self.isUnion:
            return self.alignof(is64bit)
        else:
            for size, _, member in self.offsets(is64bit):
                if member is None:
                    return size
    
    def offsets(self, is64bit=False):
        """
        Return an iterable of offsets and bit-offsets of each member in the
        struct. In the end, the size of the struct will be produced with member
        being ``None``. Example::
        
            from objctype2.types import *
            stru = Struct('CGPoint')
            stru.append(Primitive(FLOAT), 'x')
            stru.append(Primitive(FLOAT), 'y')
            stru.freeze()
            for offset, bitOffset, member in stru.offsets():
                if member:
                    print (offset, '->', member.encode())
                else:
                    print ('size of struct = ', offset)
            # prints: 0 -> "x"f
            #         4 -> "y"f
            #         size of struct = 8
        """
        
        if self.isUnion:
            maxSize = 1
            for member in self.members:
                yield (0, 0, member)
                theSize = member.baseType.sizeof(is64bit)
                if theSize > maxSize:
                    maxSize = theSize
            yield (maxSize, 0, None)
        
        else:
            offset = 0
            bitBin = 0
            maxalign = 1
            for member in self.members:
                baseType = member.baseType
                nonBitField = not isinstance(baseType, Bitfield)
                alignment = baseType.alignof(is64bit)
                if alignment > maxalign:
                    maxalign = alignment
                
                # step 1: fix the current offset and bit-offset to fit the alignment.
                if nonBitField:
                    if bitBin:
                        offset += (bitBin + 7) >> 3
                        bitBin = 0
                    offset = ((offset-1) | (alignment-1)) + 1
                    # ^ round offset up to the nearest multiple of alignment
                else:
                    if bitBin + baseType.bits > 32:
                        offset += 4
                        bitBin = 0
                
                yield (offset + (bitBin>>3), bitBin&7, member)

                # step 2: find the next offset.
                if nonBitField:
                    offset += baseType.sizeof(is64bit)
                else:
                    bitBin += baseType.bits
            
            # yield the size of struct.

            if bitBin:
                offset += 4
            offset = ((offset-1) | (maxalign-1)) + 1

            yield (offset, 0, None)

    def __hash__(self):
        return hash((self.name, self.isUnion, self.members))


if __name__ == '__main__':
    def assertEqual(x, y, msg=''):
        assert x == y, 'Unexpected {0!r} != {1!r} ... {2}'.format(x, y, msg)
    def assertNotEqual(x, y, msg=''):
        assert x != y, 'Unexpected {0!r} == {1!r} ... {2}'.format(x, y, msg)

    from itertools import zip_longest

    flt = Primitive(FLOAT)
    cls = Primitive(CLASS)
    assertEqual(flt.sizeof(is64bit=False), 4)
    assertEqual(flt.sizeof(is64bit=True), 4)
    assertEqual(cls.sizeof(is64bit=False), 4)
    assertEqual(cls.sizeof(is64bit=True), 8)
    assertEqual(flt.alignof(is64bit=False), 4)
    assertEqual(flt.alignof(is64bit=True), 4)
    assertEqual(cls.alignof(is64bit=False), 4)
    assertEqual(cls.alignof(is64bit=True), 8)
    assertEqual(flt.encode(), 'f')
    assertEqual(cls.encode(), '#')
    assertEqual(flt.primitive, FLOAT)
    assertEqual(cls.primitive, CLASS)
    assertNotEqual(flt, cls)
    assertEqual(flt, Primitive(FLOAT))

    fltptr = Unary(POINTER, flt)
    fltcmplx = Unary(COMPLEX, flt)
    fltbyref = Unary(BYREF, flt)
    assertEqual(fltptr.sizeof(is64bit=False), 4)
    assertEqual(fltptr.sizeof(is64bit=True), 8)
    assertEqual(fltptr.alignof(is64bit=False), 4)
    assertEqual(fltptr.alignof(is64bit=True), 8)
    assertEqual(fltcmplx.sizeof(is64bit=False), 8)
    assertEqual(fltcmplx.sizeof(is64bit=True), 8)
    assertEqual(fltcmplx.alignof(is64bit=False), 4)
    assertEqual(fltcmplx.alignof(is64bit=True), 4)
    assertEqual(fltbyref.sizeof(is64bit=False), 4)
    assertEqual(fltbyref.sizeof(is64bit=True), 4)
    assertEqual(fltbyref.alignof(is64bit=False), 4)
    assertEqual(fltbyref.alignof(is64bit=True), 4)
    assertEqual(fltptr.encode(), '^f')
    assertEqual(fltcmplx.encode(), 'jf')
    assertEqual(fltbyref.encode(), 'Rf')
    assertEqual(fltptr.modifier, POINTER)
    assertEqual(fltcmplx.modifier, COMPLEX)
    assertEqual(fltbyref.modifier, BYREF)
    assertEqual(fltptr.baseType, flt)
    assertEqual(fltcmplx.baseType, flt)
    assertEqual(fltbyref.baseType, flt)
    
    fltcmplxptr = Unary(POINTER, fltcmplx)
    assertEqual(fltcmplxptr.encode(), '^jf')
    assertNotEqual(fltcmplxptr, fltptr)
    assertNotEqual(fltcmplxptr, fltcmplx)
    assertNotEqual(fltcmplxptr, flt)
    assertEqual(fltcmplxptr, Unary(POINTER, Unary(COMPLEX, Primitive(FLOAT))))
    assertEqual(fltcmplxptr.baseType, fltcmplx)
    
    fltcmplxarr = Array(72, fltcmplx)
    assertEqual(fltcmplxarr.encode(), '[72jf]')
    assertEqual(fltcmplxarr.sizeof(), 72 * 8)
    assertEqual(fltcmplxarr.alignof(), 4)
    assertNotEqual(fltcmplxarr, flt)
    assertNotEqual(fltcmplxarr, fltcmplx)
    assertNotEqual(fltcmplxarr, Array(72, flt))
    assertNotEqual(fltcmplxarr, Array(56, fltcmplx))
    assertEqual(fltcmplxarr, Array(72, fltcmplx))
    assertEqual(fltcmplxarr.length, 72)
    assertEqual(fltcmplxarr.baseType, fltcmplx)
    
    nsobj = ObjCType('NSObject')
    id_ = ObjCType()
    uitbldel = ObjCType(protocols=['UITableViewDelegate', 'UITableViewDataSource'])
    nsobjtbldel = ObjCType('NSObject', ['UITableViewDelegate', 'UITableViewDataSource', 'UITableViewDataSource'])
    assertEqual(id_.encode(), '@')
    assertEqual(nsobj.encode(), '@"NSObject"')
    assertEqual(uitbldel.encode(), '@"<UITableViewDataSource,UITableViewDelegate>"')
    assertEqual(nsobjtbldel.encode(), '@"NSObject<UITableViewDataSource,UITableViewDelegate>"')
    assertNotEqual(id_, nsobj)
    assertNotEqual(nsobj, nsobjtbldel)
    assertNotEqual(nsobjtbldel, uitbldel)
    assertNotEqual(uitbldel, id_)
    assertNotEqual(id_, Primitive(BLOCK))
    assertEqual(id_.sizeof(is64bit=False), 4)
    assertEqual(id_.sizeof(is64bit=True), 8)
    assertEqual(id_.alignof(is64bit=False), 4)
    assertEqual(id_.alignof(is64bit=True), 8)
    assert id_.name is None
    assert not id_.protocols
    assertEqual(nsobj.name, 'NSObject')
    assert not nsobj.protocols
    assert uitbldel.name is None
    assertEqual(uitbldel.protocols, ('UITableViewDataSource', 'UITableViewDelegate'))
    assertEqual(nsobjtbldel.name, 'NSObject')
    assertEqual(nsobjtbldel.protocols, ('UITableViewDataSource', 'UITableViewDelegate'))
    
    bf = Bitfield(3)
    assertEqual(bf.bits, 3)
    assertEqual(bf, Bitfield(3))
    assertNotEqual(bf, id_)
    assertEqual(bf.encode(), 'b3')
    assertEqual(bf.sizeof(True), 4)
    assertEqual(bf.alignof(True), 4)
    assertEqual(bf.sizeof(False), 4)
    assertEqual(bf.alignof(False), 4)
    
    #    struct PairOfInt { int x; int y; };
    #    
    #    struct Foo {
    #    	float a;
    #    	float b;
    #    	float c;
    #    	_Complex float cf;
    #    	NSObject* obj;
    #    	int bf1 : 3;
    #    	int bf2 : 3;
    #    	int bf3 : 3;
    #    	int bf4 : 3;
    #    	int bf5 : 23;
    #    	int bf55 : 31;
    #    	int bf6 : 1;
    #    	BOOL bl;
    #    	char ch;
    #    	float fa[72];
    #    	struct PairOfInt rng;
    #    	int bf7 : 3;
    #    	_Complex float (*parr)[72];
    #    	float w;
    #    };
    
    stru = Struct('Foo')
    memberinfo = [
        {"typ":flt, "name":'a', "offset32":0, "bitoff32":0, "offset64":0, "bitoff64":0},
        {"typ":flt, "name":'b', "offset32":4, "bitoff32":0, "offset64":4, "bitoff64":0},
        {"typ":flt, "name":'c', "offset32":8, "bitoff32":0, "offset64":8, "bitoff64":0},
        {"typ":fltcmplx, "name":'cf', "offset32":0xc, "bitoff32":0, "offset64":12, "bitoff64":0},
        {"typ":nsobj, "name":'obj', "offset32":0x14, "bitoff32":0, "offset64":24, "bitoff64":0},
        {"typ":bf, "name":'bf1', "offset32":0x18, "bitoff32":0, "offset64":32, "bitoff64":0},
        {"typ":bf, "name":'bf2', "offset32":0x18, "bitoff32":3, "offset64":32, "bitoff64":3},
        {"typ":bf, "name":'bf3', "offset32":0x18, "bitoff32":6, "offset64":32, "bitoff64":6},
        {"typ":bf, "name":'bf4', "offset32":0x19, "bitoff32":1, "offset64":33, "bitoff64":1},
        {"typ":Bitfield(23), "name":'bf5', "offset32":0x1c, "bitoff32":0, "offset64":36, "bitoff64":0},
        {"typ":Bitfield(31), "name":'bf55', "offset32":0x20, "bitoff32":0, "offset64":40, "bitoff64":0},
        {"typ":Bitfield(1), "name":'bf6', "offset32":0x23, "bitoff32":7, "offset64":43, "bitoff64":7},
        {"typ":Primitive(BOOL), "name":'bl', "offset32":0x24, "bitoff32":0, "offset64":44, "bitoff64":0},
        {"typ":Primitive(CHAR), "name":'ch', "offset32":0x25, "bitoff32":0, "offset64":45, "bitoff64":0},
        {"typ":Array(72, flt), "name":'fa', "offset32":0x28, "bitoff32":0, "offset64":48, "bitoff64":0},
        {"typ":Struct('PairOfInt').append(Primitive(INT), 'x').append(Primitive(INT), 'y').freeze(),
            "name":'rng', "offset32":0x148, "bitoff32":0, "offset64":336, "bitoff64":0},
        {"typ":bf, "name":'bf7', "offset32":0x150, "bitoff32":0, "offset64":344, "bitoff64":0},
        {"typ":Unary(POINTER, fltcmplxarr), "name":'parr',
            "offset32":0x154, "bitoff32":0, "offset64":352, "bitoff64":0},
        {"typ":flt, "name":'w', "offset32":0x158, "bitoff32":0, "offset64":360, "bitoff64":0},
        {"typ":None, "name":None, "offset32":0x15c, "bitoff32":0, "offset64":368, "bitoff64":0},
    ]
    
    for info in memberinfo[:-1]:
        stru.append(info["typ"], name=info["name"])
    stru.freeze()
    
    excThrown = False
    try:
        stru.append(flt, 'more')
    except AttributeError:
        excThrown = True
    assert excThrown

    assertNotEqual(stru, Struct('Foo'))
    assertNotEqual(stru, Struct('Foo').append(Primitive(FLOAT), 'a'))
    assertEqual(stru.name, 'Foo')
    assert not stru.isUnion
    assert all(mem.baseType == info['typ'] for mem, info in zip_longest(stru.members, memberinfo[:-1]))
    assertEqual(stru.encode(), '{Foo="a"f"b"f"c"f"cf"jf"obj"@"NSObject""bf1"b3"bf2"b3"bf3"b3"bf4"b3"bf5"b23"bf55"b31"bf6"b1"bl"c"ch"c"fa"[72f]"rng"{PairOfInt="x"i"y"i}"bf7"b3"parr"^[72jf]"w"f}')
    for (offset, bitoff, mem), info in zip_longest(stru.offsets(is64bit=False), memberinfo):
        if mem is not None:
            assertEqual(mem.name, info['name'], 'member = {0!r}'.format(mem))
            assertEqual(mem.baseType, info['typ'], 'member = {0!r}'.format(mem))
        assertEqual(offset, info['offset32'], 'member = {0!r}'.format(mem))
        assertEqual(bitoff, info['bitoff32'], 'member = {0!r}'.format(mem))
    
    for (offset, bitoff, mem), info in zip_longest(stru.offsets(is64bit=True), memberinfo):
        if mem is not None:
            assertEqual(mem.name, info['name'], 'member = {0!r}'.format(mem))
            assertEqual(mem.baseType, info['typ'], 'member = {0!r}'.format(mem))
        assertEqual(offset, info['offset64'], 'member = {0!r}'.format(mem))
        assertEqual(bitoff, info['bitoff64'], 'member = {0!r}'.format(mem))

    assertEqual(stru.alignof(is64bit=False), 4)
    assertEqual(stru.alignof(is64bit=True), 8)
    assertEqual(stru.sizeof(is64bit=False), 0x15c)
    assertEqual(stru.sizeof(is64bit=True), 368)


    
    stru2 = Struct()
    for info in memberinfo[:-1]:
        stru2.append(info["typ"])
    stru2.freeze()
    
    for (offset, bitoff, mem), info in zip_longest(stru2.offsets(is64bit=True), memberinfo):
        if mem is not None:
            assert mem.name is None, 'member = {0!r}'.format(mem)
            assertEqual(mem.baseType, info['typ'], 'member = {0!r}'.format(mem))
        assertEqual(offset, info['offset64'], 'member = {0!r}'.format(mem))
        assertEqual(bitoff, info['bitoff64'], 'member = {0!r}'.format(mem))
    
    assertEqual(stru2.sizeof(is64bit=False), 0x15c)
    assertEqual(stru2.sizeof(is64bit=True), 368)
    assertEqual(stru2.alignof(is64bit=False), 4)
    assertEqual(stru2.alignof(is64bit=True), 8)
    assertEqual(stru2.encode(), '{?=fffjf@"NSObject"b3b3b3b3b23b31b1cc[72f]{PairOfInt="x"i"y"i}b3^[72jf]f}')
    assertNotEqual(stru2, stru)
    assertNotEqual(flt, stru2)
    assertEqual(stru2, stru2)
    assertEqual(stru2.name, '?')
    assert not stru2.isUnion
    assert all(mem.baseType == info['typ'] for mem, info in zip_longest(stru2.members, memberinfo[:-1]))
    
    union = Struct(isUnion=True)
    for info in memberinfo[:-1]:
        union.append(info["typ"])
    union.freeze()
    
    for (offset, bitoff, mem), info in zip_longest(union.offsets(is64bit=True), memberinfo):
        if mem is not None:
            assert mem.name is None, 'member = {0!r}'.format(mem)
            assertEqual(mem.baseType, info['typ'], 'member = {0!r}'.format(mem))
            assertEqual(offset, 0, 'member = {0!r}'.format(mem))
            assertEqual(bitoff, 0, 'member = {0!r}'.format(mem))
        else:
            assertEqual(offset, 72*4)
            assertEqual(bitoff, 0)
    
    assertEqual(union.sizeof(is64bit=True), 8)
    assertEqual(union.sizeof(is64bit=False), 4)
    assertEqual(union.alignof(is64bit=True), 8)
    assertEqual(union.alignof(is64bit=False), 4)
    assertEqual(union.encode(), '(?=fffjf@"NSObject"b3b3b3b3b23b31b1cc[72f]{PairOfInt="x"i"y"i}b3^[72jf]f)')
    assertNotEqual(union, stru2)
    assertEqual(union.name, '?')
    assert union.isUnion
    assert all(mem.baseType == info['typ'] for mem, info in zip_longest(union.members, memberinfo[:-1]))
    
    assertEqual(Struct().append(Bitfield(1)).freeze().sizeof(), 4)
    
    set([flt, fltcmplxptr, stru2])
    