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

from collections import namedtuple
import sys

class _Piece(object):
    def __init__(self, rightShift, bias=0):
        self.mask = 1 << bias
        self.rightShift = rightShift - bias
        
    def addBit(self):
        self.mask = self.mask << 1 | self.mask


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
    
    >>> from bitpattern import BitPattern
    >>> spsrPat = BitPattern('NZCVQttJ____ggggttttttEAIFTMMMMM')
    >>> spsrPat.unpack(     0b01011101000011010101011101010111)
    BitPatternResult(A=1, C=0, E=1, g=13, F=1, I=0, J=1, M=23, N=0, Q=1, T=0, V=1, Z=1, t=149)
    >>> res = _
    >>> list(map(bin, [res.g, res.t, res.M]))
    ['0b1101', '0b10010101', '0b10111']
    >>> bin(spsrPat.pack(res))
    '0b1011101000011010101011101010111'
    
    
    .. attribute:: returnType
    
        A type which indicates the return type received by :meth:`unpack`.
    
    .. attribute:: pattern
    
        The input bit pattern.
    
    '''

    def __init__(self, pattern):
        pass
        
    def unpack(self, integer):
        'Unpack an integer into bits. Returns ``None`` if fails to verify.'
        if (integer & self._verifyMask) != self._verifyBits:
            return None
        
        resDict = {}
        for character, pieces in self._pieces:
            result = 0
            for piece in pieces:
                result |= (integer >> piece.rightShift) & piece.mask
            resDict[character] = result
        
        return self.returnType(**resDict)

    def pack(self, bitres):
        'Pack bits back into an integer.'
        result = self._verifyBits
        for character, pieces in self._pieces:
            bits = getattr(bitres, character)
            for piece in pieces:
                result |= (bits & piece.mask) << piece.rightShift
        return result

if 'sphinx-build' not in sys.argv[0]:
    def BitPattern_init(self, pattern):
        self.pattern = pattern
    
        verifyMask = 0
        verifyBits = 0
        characterPieces = {}
        
        lastCharacter = '_'
        
        for rightShift, char in enumerate(reversed(pattern)):
            if char in '01':
                verifyMask |= 1 << rightShift
                if char == '1':
                    verifyBits |= 1 << rightShift
            elif 'a' <= char <= 'z' or 'A' <= char <= 'Z':
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
            
        self.returnType = namedtuple('BitPatternResult', characterPieces.keys())
        self._verifyMask = verifyMask
        self._verifyBits = verifyBits
        self._pieces = list(characterPieces.items())
        
    BitPattern.__init__ = BitPattern_init


if __name__ == '__main__':
    bitPattern = 'aaabbccb_01_d1f0'
    bitValue1 = 0b1011011100101100
    bitValue2 = 0b0101110111101110
    
    parser = BitPattern(bitPattern)
    assert parser.unpack(bitValue2) is None
    
    res = parser.unpack(bitValue1)
    assert res.a == 0b101
    assert res.b == 0b101
    assert res.c == 0b11
    assert res.d == 1
    assert res.f == 0
    
    assert parser.pack(res) == bitValue1
            