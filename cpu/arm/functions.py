#    
#    functions.py ... ARM functions
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

(SRTYPE_LSL, SRTYPE_LSR, SRTYPE_ASR, SRTYPE_ROR, SRTYPE_RRX) = range(5)
(REG_SP, REG_LR, REG_PC) = (13, 14, 15)
COND_NONE = 15

def signed(notmask, x):
    '''Make *x* a signed number. *notmask* should be set to ``-1<<N`` where *N*
    is the number of bits *x* should have.
    
    For a special pointer, it always return itself.'''
    if x & notmask>>1:
        x += notmask
    return x



def fixPCAddrBX(pcAddr):
    '''Fix *pcAddr* into a valid instruction address, with possibility of
    changing instruction set. Return a tuple of the fixed address and whether 
    it will run in Thumb mode or not.'''
    
    if pcAddr & 1:
        return (pcAddr-1, True)
    else:
        return (pcAddr&~3, False)

def fixPCAddrB(pcAddr, thumbMode):
    'Fix *pcAddr* into a valid instruction address.'
    notmask = ~1 if thumbMode else ~3
    return pcAddr & notmask

def fixPCAddrLoad(pcAddr, thumbMode):
    '''Fix *pcAddr* using ARM ARM's ``LoadWritePC`` algorithm. Return a tuple of
    the fixed address and whether it will run in Thumb mode or not.'''
    return fixPCAddrBX(pcAddr)

def fixPCAddrALU(pcAddr, thumbMode):
    '''Fix *pcAddr* using ARM ARM's ``ALUWritePC`` algorithm. Return a tuple of
    the fixed address and whether it will run in Thumb mode or not.'''
    if thumbMode:
        return (pcAddr & ~1, True)
    else:
        return fixPCAddrBX(pcAddr)

    

def LSL_C(mask, x, shift):
    "ARM ARM's ``LSL_C`` function. Here, *mask* should be set to ``(1<<N)-1``."
    x <<= shift
    return (x & mask, not not(x & (mask+1)))

def LSL(mask, x, shift):
    "ARM ARM's ``LSL`` function. Here, *mask* should be set to ``(1<<N)-1``."
    return (x << shift) & mask

def LSR_C(mask, x, shift):
    """ARM ARM's ``LSR_C`` function. Here, *mask* should be set to ``(1<<N)-1``,
    and *shift* must be positive (1 or above)."""
    x >>= shift-1
    return (x >> 1, x & 1)

def LSR(mask, x, shift):
    "ARM ARM's ``LSR`` function. Here, *mask* should be set to ``(1<<N)-1``."
    return x >> shift

def ASR_C(mask, x, shift):
    """ARM ARM's ``ASR_C`` function. Here, *mask* should be set to ``(1<<N)-1``,
    and *shift* must be positive (1 or above)."""
    x = signed(~mask, x) >> (shift-1)
    return ((x >> 1) & mask, x & 1)

def ASR(mask, x, shift):
    "ARM ARM's ``ASR`` function. Here, *mask* should be set to ``(1<<N)-1``."
    return (signed(~mask, x) >> shift) & mask

def ROR_C(mask, x, shift):
    """ARM ARM's ``ROR_C`` function. Here, *mask* should be set to ``(1<<N)-1``,
    and *shift* must be between 0 and *N*."""
    res = (x*(2+mask)) >> shift
    return (res & mask, not not(res & (mask+1)>>1))

def ROR(mask, x, shift):
    """ARM ARM's ``ROR`` function. Here, *mask* should be set to ``(1<<N)-1``
    and *shift* must be between 0 and *N*."""
    return ((x*(2+mask)) >> shift) & mask

def RRX_C(mask, x, carry):
    "ARM ARM's ``RRX_C`` function. Here, *mask* should be set to ``(1<<N)-1``."
    x += carry*(1+mask)
    return (x >> 1, x & 1)

def RRX(mask, x, carry):
    "ARM ARM's ``RRX`` function. Here, *mask* should be set to ``(1<<N)-1``."
    return (x + carry*(1+mask)) >> 1

def DecodeImmShift(rawShiftType, imm):
    "ARM ARM's ``DecodeImmShift`` function."
    if rawShiftType != SRTYPE_LSL:
        if not imm:
            if rawShiftType == SRTYPE_ROR:
                rawShiftType = SRTYPE_RRX
                imm = 1
            else:
                imm = 32
    return (rawShiftType, imm)

def Shift_C(mask, value, shiftType, shiftAmount, carry):
    "ARM ARM's ``Shift_C`` function. Here, *mask* should be set to ``(1<<N)-1``."
    if shiftAmount:
        if shiftType == SRTYPE_RRX:
            return RRX_C(mask, value, carry)
        else:
            return (LSL_C, LSR_C, ASR_C, ROR_C)[shiftType](mask, value, shiftAmount)
    else:
        return (value, carry)

def Shift(mask, value, shiftType, shiftAmount, carry):
    "ARM ARM's ``Shift`` function. Here, *mask* should be set to ``(1<<N)-1``."
    if shiftType == SRTYPE_RRX:
        return RRX(mask, value, carry)
    else:
        return (LSL, LSR, ASR, ROR)[shiftType](mask, value, shiftAmount)

def ThumbExpandImm_C(imm, carry):
    "ARM ARM's ``ThumbExpandImm_C`` function."
    
    top2 = imm >> 10
    if not top2:
        middle2 = imm >> 8
        if middle2 == 0:
            retval = imm
        else:
            bottom8 = imm & 0xff
            retval = 0
            lopart = bottom8 | bottom8 << 16
            if middle2 & 1:
                retval = lopart
            if middle2 & 2:
                retval |= lopart << 8
        return (retval, carry)
    else:
        lshift = 32 - (imm >> 7)
        res = (0x80 + (imm & 0x7f)) << lshift
        return (res, lshift == 24)

def ThumbExpandImm(imm):
    "ARM ARM's ``ThumbExpandImm`` function."
    return ThumbExpandImm_C(imm, 0)[0]

def ARMExpandImm_C(imm, carry):
    "ARM ARM's ``ARMExpandImm_C`` function."
    amount = (imm >> 8) * 2
    if not amount:
        return (imm, carry)
    else:
        imm &= 0xff
        if amount < 8:
            imm = ((imm * 0x100000001) >> amount) & 0xffffffff
            return (imm, imm >> 31)
        else:
            imm <<= 32-amount
            return (imm, imm >> 31)

def ARMExpandImm(imm):
    "ARM ARM's ``ARMExpandImm`` function."
    return ROR(0xffffffff, imm & 0xff, (imm >> 8) * 2)

def AddWithCarry(mask, x, y, carry):
    "ARM ARM's ``AddWithCarry`` function."
    notmask = ~mask
    usum = x + y + carry
    ssum = signed(notmask, x) + signed(notmask, y) + carry
    carry = not not (usum & notmask)
    #^ 'usum > mask' would be more efficient, but SpecialPointer doesn't support
    #   such comparison.
    usum &= mask
    overflow = ssum != signed(notmask, usum)
    return (usum, carry, overflow)



def ITAdvance(itstate):
    "ARM ARM's ``ITAdvance`` function."
    return (itstate & 0b111) and ((itstate & 0b11100000) + ((itstate&0b1111)*2))



