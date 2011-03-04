#    
#    bitpattern.py ... Parse bits
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
#

import sys
from keyword import iskeyword
import re


__all__ = ['InvalidBitPatternError', 'UnmatchBitPatternError', 'BitPattern']

class _Piece(object):
    def __init__(self, rightShift, bias=0):
        self.mask = 1 << bias
        self.rightShift = rightShift - bias
        
    def addBit(self):
        self.mask = self.mask << 1 | self.mask



_isident = re.compile(r'^[_a-zA-Z]\w*$').match


class UnmatchBitPatternError(Exception):
    def __init__(self, value, pattern):
        self.value = value
        self.pattern = pattern
    def __str__(self):
        return 'Cannot match value 0x{0:x} with bit pattern {1!r}'.format(self.value, self.pattern)


# does this really work???
def _vermicelli(pattern, fields, className):
    if not className:
        clsname = "BitPatternResult"

    # sanity check
    for fieldname in fields:
        if not _isident(fieldname):
            raise ValueError('Field names should be an identifier: ' + repr(fieldname))
        elif fieldname[0] == '_':
            raise ValueError('Field names cannot start with an underscore "_": ' + repr(fieldname))
        elif iskeyword(fieldname) or fieldname == 'value':
            raise ValueError('Field names cannot be a keyword or "value": ' + repr(fieldname))
    if len(set(fields)) < len(fields):
        raise ValueError('Some field names are duplicated.')
    
    if not _isident(className):
        raise ValueError('Class name should be an identifier: ' + repr(clsname))
    elif iskeyword(className):
        raise ValueError('Class name cannot be a keyword: ' + repr(clsname))
    # end sanity check
    
    fieldtuple = tuple(fields)
    
    eqstring = ''.join(map(' and self.{0}==other.{0}'.format, fieldtuple))
    formatargs = ', '.join(map('{0}={{0.{0}}}'.format, fieldtuple))
    tupleargs = ''.join(map('self.{0},'.format, fieldtuple))
    
    classStr = '''

class {className}(object):
    __slots__ = {fieldtuple!r}
    _parser = None    
    
    def __init__(self, value=None):
        if value is not None:
            if not self._parser.unpackInto(value, self):
                raise _UnmatchBitPatternError(value, self._parser.pattern)
    
    @property
    def value(self):
        return self._parser.pack(self)
    
    def __eq__(self, other):
        return isinstance(other, type(self)){eqstring}
    def _astuple(self):
        return ({tupleargs})
    def hash(self):
        return hash(({tupleargs}))
    def __repr__(self):
        return '{className}({formatargs})'.format(self)

'''.format(className=className, fieldtuple=fieldtuple, eqstring=eqstring, tupleargs=tupleargs, formatargs=formatargs)
    
    namespace = {'__name__': '_BitPatternResult_' + className, '_UnmatchBitPatternError': UnmatchBitPatternError}
    try:
        exec(classStr, namespace)
    except SyntaxError as e:
        raise SyntaxError(e.msg + ':\n' + classStr) from e
    
    result = namespace[className]
    try:
        result._parser = pattern
        result.__module__ = sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return result




class InvalidBitPatternError(Exception):
    'This exception will be raised when the bit pattern contains an invalid character.'
    def __init__(self, character):
        self.character = character
    def __str__(self):
        return 'Character {0!r} is invalid in a bit pattern.'.format(character)


class BitPattern(object):
    '''
    This class provides methods to convert between a bit structure and the
    packed integer.
    
    The *pattern* should provde a string for the expected bit pattern, where:
    
    * ``0``: A zero must appear in that bit
    * ``1``: A one must appear in that bit
    * ``_``: Ignore this bit
    * ``a``-``z``, ``A``-``Z``: Store this bit into a member labeled by it.
    
    * Space: Separator, ignored by this parser.
    
    Example::
    
        from bitpattern import BitPattern
        
        def __fixIT(t):
            return [(t>>2) & 14, (t>>6) + (t&7)*4]
        
        def __unfixIT(tp):
            p = tp[1]
            return (tp[0]*4) + ((p&3)*64) + (p>>2)
            
        spsrPat = BitPattern('NZCVQttJ ____gggg ttttttEA IFTMMMMM',
                            rename={'g':'GE', 't':'IT'},
                            fixUps={'IT':(__fixIT,__unfixIT)},
                            className='Status')
                
        res = spsrPat.unpack(0b01011101000011010101011101010111)
        print(res)
        # Status(A=1, C=0, E=1, F=1, I=0, J=1, M=23, IT=[4, 22], N=0, Q=1, GE=13, T=0, V=1, Z=1)
        print(res.IT)
        # [4, 22]
        print(bin(spsrPat.pack(res)))
        # 0b1011101000011010101011101010111
    
    
    .. attribute:: returnType
    
        A type which indicates the return type received by :meth:`unpack`.
        
        The returned type contains a special property ``value``, which is 
        equivalent to calling :meth:`pack` on the instance.
    
    .. attribute:: pattern
    
        The input bit pattern.
        
    .. attribute:: rename
    
        Renaming dictionary.
        
        Since a bit can only be represented by 1 character, often the actual
        name is not what you are desired. Therefore, you could provide this 
        dictionary to replace those character into the actual name in the 
        resulting tuple.
        
    .. attribute:: fixUps
    
        A dictionary of tuple of functions that will be applied after and before
        calling :meth:`unpack` and :meth:`pack` respectively.
        
        Sometimes the parsed bits are still not in the required format. You
        could use this dictionary to perform a final make-up of those bits. The
        keys should be the renamed fields, the first function should take an
        integer (representing the parsed bits) as input and return the fixed
        result (any object) as output, and the second function should reverse
        the action of the first.
        
    .. attribute:: className
    
        The class name of :attr:`returnType`. This only affects the
        documentation and ``__str__``/``__repr__`` of the type.
    
    '''

    def __init__(self, pattern, rename=None, fixUps=None, className='BitPatternResult'):
        self.pattern = pattern
        if not rename:
            rename = {}
        self.rename = rename
        self.fixUps = fixUps or {}
    
        verifyMask = 0
        verifyBits = 0
        characterPieces = {}
        
        lastCharacter = '_'
        rightShift = 0
        
        for char in reversed(pattern):
            if char == ' ':
                continue
            elif char in '01':
                verifyMask += 1 << rightShift
                if char == '1':
                    verifyBits += 1 << rightShift
            elif 'a' <= char <= 'z' or 'A' <= char <= 'Z':
                if char in rename:
                    char = rename[char]
                if char != lastCharacter:
                    if char not in characterPieces:
                        characterPieces[char] = [_Piece(rightShift)]
                    else:
                        cpc = characterPieces[char]
                        bias = cpc[-1].mask.bit_length()
                        cpc.append(_Piece(rightShift, bias))
                else:
                    characterPieces[char][-1].addBit()
            elif char != '_':
                raise InvalidBitPatternError(char)
            
            lastCharacter = char
            rightShift += 1
            
        # self.returnType = namedtuple(className, characterPieces.keys())
        self.returnType = _vermicelli(self, characterPieces.keys(), className)
        self._verifyMask = verifyMask
        self._verifyBits = verifyBits
        self._pieces = list(characterPieces.items())
        
    def unpackInto(self, integer, object):
        '''Unpack an integer into bits, and set the attributes of *object* with
        the fields. Returns ``False`` if *integer* fails to verify.'''
        if (integer & self._verifyMask) != self._verifyBits:
            return False
        
        fixUps = self.fixUps
        for character, pieces in self._pieces:
            result = 0
            for piece in pieces:
                result |= (integer >> piece.rightShift) & piece.mask
            if character in fixUps:
                result = fixUps[character][0](result)
            setattr(object, character, result)
        return True
        
    def unpack(self, integer):
        'Unpack an integer into bits. Returns ``None`` if fails to verify.'
        rv = self.returnType()
        if self.unpackInto(integer, rv):
            return rv
        else:
            return None

    def pack(self, bitres):
        'Pack bits back into an integer.'
        result = self._verifyBits
        fixUps = self.fixUps
        for character, pieces in self._pieces:
            bits = getattr(bitres, character)
            if character in fixUps:
                bits = fixUps[character][1](bits)
            for piece in pieces:
                result |= (bits & piece.mask) << piece.rightShift
        return result
        
    def __repr__(self):
        base = [repr(self.pattern)]
        if self.rename:
            base.append('rename=' + repr(self.rename))
        if self.fixUps:
            base.append('fixUps=' + repr(self.rename))
        if self.className != 'BitPatternResult':
            base.append('className=' + repr(self.className))
        return '{0}({1})'.format(type(self).__name__, ', '.join(base))

    def __str__(self):
        return '{0}({1})'.format(type(self).__name__, self.pattern)


if __name__ == '__main__':
    bitPattern = 'aaabbcc b_01_d1f0'
    bitValue1 = 0b1011011100101100
    bitValue2 = 0b0101110111101110
    
    parser = BitPattern(bitPattern, rename={'b':'omg'}, fixUps={'a':(str,int)})
    assert parser.unpack(bitValue2) is None
    
    res = parser.unpack(bitValue1)
    assert res.a == '5'
    assert res.omg == 0b101
    assert res.c == 0b11
    assert res.d == 1
    assert res.f == 0
    try:
        res.b
    except AttributeError:
        pass
    else:
        assert False
    
    assert parser.pack(res) == bitValue1
    res.a = 3
    assert res.a == 3
    assert parser.pack(res) == 0b0111011100101100
    assert res.value == 0b0111011100101100
    
    assert not parser.unpackInto(bitValue2, res)
    
    try:
        BitPattern('abc!')
    except InvalidBitPatternError as e:
        assert e.character == '!'
    else:
        assert False

