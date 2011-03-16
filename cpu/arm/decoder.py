#    
#    decoder.py ... ARM instruction decoders
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

from bitpattern import BitPattern
from functools import wraps
from itertools import chain
from cpu.arm.instruction import Instruction, Condition
from cpu.arm.functions import COND_NONE

_decoders = {
    (4,0):[],
    (2,1):[],
    (4,1):[],
    (2,3):[],
    (4,3):[],
}

class InstructionDecoderNotFoundError(Exception):
    '''This exception is raised when :class:`InstructionDecoder` fails to find a
    suitable decoder to decode a byte sequence.'''
    def __init__(self, encoding, length, instructionSet):
        fmt = "Cannot decode {2} instruction {0:#0{1}x} [{0:0{3}b}]."
        isetName = ('ARM', 'Thumb', 'Jazelle', 'Thumb-EE')[instructionSet]
        bitLength = length*8 if instructionSet else 28
        super().__init__(fmt.format(encoding, bitLength>>2, isetName, bitLength))


class InstructionDecoder(object):
    '''A decorator to convert a function into an instruction decoder. You should
    supply the instruction length, instruction set and bit pattern which the
    collection of instructions the decorated function can decode. The decorated
    function's signature must be::
    
        def f(res: "Decoded struct", encoding, condition) -> Instruction:
            ...
    
    If the function cannot handle *res*, it should return ``None``.

    When this method is called with an ARM instruction, the condition code will
    *not* be included along the encoding, i.e. the *pattern* should only be
    28-bit in size. If the decoder is handling an unconditional instruction
    (i.e. the condition code must always be
    :const:`~cpu.arm.functions.COND_NONE`), the user should supply ``True`` to
    the optional parameter ``unconditional``.

    .. attribute:: unconditional
    
        Whether this instruction does not have the condition field. This is
        applicable to ARM instruction decoders only.
        
    '''
    
    @staticmethod
    def decoders(length, instructionSet):
        'Get an iterable of decoders for a given instruction set and encoding length.'
        if instructionSet == 3:
            return chain(_decoders[(length, 3)], _decoders[(length, 1)])
        else:
            return _decoders[(length, instructionSet)]
    
    
    @staticmethod
    def create(encoding, length, instructionSet, forceCondition=COND_NONE):
        '''Create an instruction using *encoding* with length *length* in
        *instructionSet*.
        
        If the instruction ought to carry a condition (e.g. due to the IT block)
        you could supply a valid condition code in *forceCondition*.'''
        
        isARM = instructionSet == 0
        cond = forceCondition
        if isARM and cond == COND_NONE:
            cond = encoding >> 28
            encoding &= 0xfffffff
        
        for decoder in InstructionDecoder.decoders(length, instructionSet):
            if isARM and decoder.unconditional != (cond == COND_NONE):
                continue
            retval = decoder(encoding, cond)
            if retval:
                retval.decoder = decoder
                break
        else:   # pragma: no cover
            raise InstructionDecoderNotFoundError(encoding, length, instructionSet)
            retval = Instruction(encoding, length, instructionSet)

        if cond != COND_NONE:
            retval.condition = Condition(cond)
        return retval


    def __init__(self, length, instructionSet, pattern, unconditional=False):
        # safe check
        assert (instructionSet == 0 and length == 4 and len(pattern) == 28) \
            or (instructionSet & 1 and length == 2 and len(pattern) == 16) \
            or (instructionSet & 1 and length == 4 and len(pattern.replace(' ','')) == 32)
    
        self.pattern = pattern
        self.unconditional = unconditional
        self.length = length
        self.instrSet = instructionSet
    
    
    def __call__(self, f):
        unpacker = BitPattern(self.pattern).unpack
    
        @wraps(f)
        def decoder(encoding, condition):
            res = unpacker(encoding)
            return res and f(res, encoding, condition)
        
        decoder.unconditional = self.unconditional
        _decoders[(self.length, self.instrSet)].append(decoder)
        
        return decoder
        
        