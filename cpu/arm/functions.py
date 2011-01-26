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


def LSL_C(mask, x, Shift):
    "ARM ARM's ``LSL_C`` function. Here, *mask* should be set to ``(1<<N)-1``."
    x <<= Shift
    return (x & mask, not not(x & (mask+1)))

def LSL(mask, x, Shift):
    "ARM ARM's ``LSL`` function. Here, *mask* should be set to ``(1<<N)-1``."
    return (x << Shift) & mask

def LSR_C(mask, x, Shift):
    "ARM ARM's ``LSR_C`` function. Here, *mask* should be set to ``(1<<N)-1``."
    x >>= Shift-1
    return (x >> 1, x & 1)

def LSR(mask, x, Shift):
    "ARM ARM's ``LSR`` function. Here, *mask* should be set to ``(1<<N)-1``."
    return x >> Shift

def ASR_C(mask, x, Shift):
    "ARM ARM's ``ASR_C`` function. Here, *mask* should be set to ``(1<<N)-1``."
    x = signed(~mask, x) >> (Shift-1)
    return ((x >> 1) & mask, x & 1)

def ASR(mask, x, Shift):
    "ARM ARM's ``ASR`` function. Here, *mask* should be set to ``(1<<N)-1``."
    return (signed(~mask, x) >> Shift) & mask

def ROR_C(mask, x, Shift):
    "ARM ARM's ``ROR_C`` function. Here, *mask* should be set to ``(1<<N)-1``."
    res = (x*(2+mask)) >> Shift
    return (res & mask, not not(res & (mask+1)>>1))

def ROR(mask, x, Shift):
    "ARM ARM's ``ROR`` function. Here, *mask* should be set to ``(1<<N)-1``."
    return ((x*(2+mask)) >> Shift) & mask

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
    overflow = ssum != signed(notmask, usum)
    carry = not not (usum & notmask)
    #^ 'usum > mask' would be more efficient, but SpecialPointer doesn't support
    #   such comparison.
    usum &= mask
    return (usum, carry, overflow)



def ITAdvance(itstate):
    "ARM ARM's ``ITAdvance`` function."
    return (itstate & 0b111) and ((itstate & 0b11100000) + ((itstate&0b1111)*2))


if __name__ == '__main__':
    assert signed(-1<<32, 0x12345678) == 0x12345678
    assert signed(-1<<32, 0x87654321) == -0x789abcdf

    assert LSL_C(0xffffffff, 0x1234, 4) == (0x12340, 0)
    assert LSL_C(0xffffffff, 0x1234, 20) == (0x23400000, 1)
    assert LSL_C(0xffffffff, 0x1234, 21) == (0x46800000, 0)
    assert LSL(0xffffffff, 0x1234, 4) == 0x12340
    assert LSL(0xffffffff, 0x1234, 20) == 0x23400000
    assert LSL(0xffffffff, 0x1234, 21) == 0x46800000
    
    assert LSR_C(0xffffffff, 0x876f0000, 4) == (0x876f000, 0)
    assert LSR_C(0xffffffff, 0x876f0000, 20) == (0x876, 1)
    assert LSR_C(0xffffffff, 0x876f0000, 21) == (0x43b, 0)
    assert LSR(0xffffffff, 0x876f0000, 4) == 0x876f000
    assert LSR(0xffffffff, 0x876f0000, 20) == 0x876
    assert LSR(0xffffffff, 0x876f0000, 21) == 0x43b
        
    assert ASR_C(0xffffffff, 0x876f0000, 4) == (0xf876f000, 0)
    assert ASR_C(0xffffffff, 0x876f0000, 20) == (0xfffff876, 1)
    assert ASR_C(0xffffffff, 0x876f0000, 21) == (0xfffffc3b, 0)
    assert ASR(0xffffffff, 0x876f0000, 4) == 0xf876f000
    assert ASR(0xffffffff, 0x876f0000, 20) == 0xfffff876
    assert ASR(0xffffffff, 0x876f0000, 21) == 0xfffffc3b
    assert ASR_C(0xffffffff, 0x789abcde, 4) == (0x0789abcd, 1)
    
    assert ROR_C(0xff, 0b11001101, 1) == (0b11100110, 1)
    assert ROR_C(0xff, 0b11001101, 2) == (0b01110011, 0)
    assert ROR_C(0xff, 0b11001101, 7) == (0b10011011, 1)
    assert ROR(0xff, 0b11001101, 1) == 0b11100110
    assert ROR(0xff, 0b11001101, 2) == 0b01110011
    assert ROR(0xff, 0b11001101, 7) == 0b10011011
    
    assert RRX_C(0xffffffff, 0x109df893, 1) == (0x884efc49, 1)
    assert RRX_C(0xffffffff, 0x109df893, 0) == (0x084efc49, 1)
    assert RRX_C(0xffffffff, 0x109df892, 0) == (0x084efc49, 0)
    assert RRX(0xffffffff, 0x109df893, 1) == 0x884efc49
    assert RRX(0xffffffff, 0x109df893, 0) == 0x084efc49
    
    assert DecodeImmShift(0, 0) == (SRTYPE_LSL, 0)
    assert DecodeImmShift(0, 9) == (SRTYPE_LSL, 9)
    assert DecodeImmShift(1, 0) == (SRTYPE_LSR, 32)
    assert DecodeImmShift(1, 9) == (SRTYPE_LSR, 9)
    assert DecodeImmShift(2, 0) == (SRTYPE_ASR, 32)
    assert DecodeImmShift(2, 9) == (SRTYPE_ASR, 9)
    assert DecodeImmShift(3, 0) == (SRTYPE_RRX, 1)
    assert DecodeImmShift(3, 9) == (SRTYPE_ROR, 9)
    
    assert Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 0, 1) == (0x1234, 1)
    assert Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 0, 0) == (0x1234, 0)
    assert Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 4, 1) == (0x12340, 0)
    assert Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 4, 0) == (0x12340, 0)
    assert Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 20, 1) == (0x23400000, 1)
    assert Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 20, 0) == (0x23400000, 1)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 0, 1) == (0x876f0000, 1)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 0, 0) == (0x876f0000, 0)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 4, 1) == (0x876f000, 0)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 4, 0) == (0x876f000, 0)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 20, 1) == (0x876, 1)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 20, 0) == (0x876, 1)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 0, 1) == (0x876f0000, 1)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 0, 0) == (0x876f0000, 0)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 4, 1) == (0xf876f000, 0)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 4, 0) == (0xf876f000, 0)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 20, 1) == (0xfffff876, 1)
    assert Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 20, 0) == (0xfffff876, 1)
    assert Shift_C(0xff, 0b11001101, SRTYPE_ROR, 0, 1) == (0b11001101, 1)
    assert Shift_C(0xff, 0b11001101, SRTYPE_ROR, 0, 0) == (0b11001101, 0)
    assert Shift_C(0xff, 0b11001101, SRTYPE_ROR, 1, 1) == (0b11100110, 1)
    assert Shift_C(0xff, 0b11001101, SRTYPE_ROR, 1, 0) == (0b11100110, 1)
    assert Shift_C(0xff, 0b11001101, SRTYPE_ROR, 2, 1) == (0b01110011, 0)
    assert Shift_C(0xff, 0b11001101, SRTYPE_ROR, 2, 0) == (0b01110011, 0)
    assert Shift_C(0xffffffff, 0x109df893, SRTYPE_RRX, 1, 1) == (0x884efc49, 1)
    assert Shift_C(0xffffffff, 0x109df893, SRTYPE_RRX, 1, 0) == (0x084efc49, 1)
    assert Shift_C(0xffffffff, 0x109df892, SRTYPE_RRX, 1, 0) == (0x084efc49, 0)
    
    assert Shift(0xffffffff, 0x1234, SRTYPE_LSL, 0, 1) == 0x1234
    assert Shift(0xffffffff, 0x1234, SRTYPE_LSL, 0, 0) == 0x1234
    assert Shift(0xffffffff, 0x1234, SRTYPE_LSL, 4, 1) == 0x12340
    assert Shift(0xffffffff, 0x1234, SRTYPE_LSL, 4, 0) == 0x12340
    assert Shift(0xffffffff, 0x1234, SRTYPE_LSL, 20, 1) == 0x23400000
    assert Shift(0xffffffff, 0x1234, SRTYPE_LSL, 20, 0) == 0x23400000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 0, 1) == 0x876f0000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 0, 0) == 0x876f0000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 4, 1) == 0x876f000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 4, 0) == 0x876f000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 20, 1) == 0x876
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 20, 0) == 0x876
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 0, 1) == 0x876f0000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 0, 0) == 0x876f0000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 4, 1) == 0xf876f000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 4, 0) == 0xf876f000
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 20, 1) == 0xfffff876
    assert Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 20, 0) == 0xfffff876
    assert Shift(0xff, 0b11001101, SRTYPE_ROR, 0, 1) == 0b11001101
    assert Shift(0xff, 0b11001101, SRTYPE_ROR, 0, 0) == 0b11001101
    assert Shift(0xff, 0b11001101, SRTYPE_ROR, 1, 1) == 0b11100110
    assert Shift(0xff, 0b11001101, SRTYPE_ROR, 1, 0) == 0b11100110
    assert Shift(0xff, 0b11001101, SRTYPE_ROR, 2, 1) == 0b01110011
    assert Shift(0xff, 0b11001101, SRTYPE_ROR, 2, 0) == 0b01110011
    assert Shift(0xffffffff, 0x109df893, SRTYPE_RRX, 1, 1) == 0x884efc49
    assert Shift(0xffffffff, 0x109df893, SRTYPE_RRX, 1, 0) == 0x084efc49
    assert Shift(0xffffffff, 0x109df892, SRTYPE_RRX, 1, 0) == 0x084efc49
    
    assert ThumbExpandImm(0x0ab) == 0x000000ab
    assert ThumbExpandImm(0x1ab) == 0x00ab00ab
    assert ThumbExpandImm(0x2ab) == 0xab00ab00
    assert ThumbExpandImm(0x3ab) == 0xabababab
    for i in range(8, 32):
        assert ThumbExpandImm(i << 7 | 0b1011010) == 0b11011010 << (32-i)        
    assert ThumbExpandImm_C(0x0ab, 0) == (0x000000ab, 0)
    assert ThumbExpandImm_C(0x1ab, 0) == (0x00ab00ab, 0)
    assert ThumbExpandImm_C(0x2ab, 0) == (0xab00ab00, 0)
    assert ThumbExpandImm_C(0x3ab, 0) == (0xabababab, 0)
    assert ThumbExpandImm_C(0x0ab, 1) == (0x000000ab, 1)
    assert ThumbExpandImm_C(0x1ab, 1) == (0x00ab00ab, 1)
    assert ThumbExpandImm_C(0x2ab, 1) == (0xab00ab00, 1)
    assert ThumbExpandImm_C(0x3ab, 1) == (0xabababab, 1)
    assert ThumbExpandImm_C(8 << 7 | 0b1011010, 0) == (0b11011010 << 24, 1)
    assert ThumbExpandImm_C(8 << 7 | 0b1011010, 1) == (0b11011010 << 24, 1)
    for i in range(9, 32):
        assert ThumbExpandImm_C(i << 7 | 0b1011010, 0) == (0b11011010 << (32-i), 0)
        assert ThumbExpandImm_C(i << 7 | 0b1011010, 1) == (0b11011010 << (32-i), 0)
        
    assert ARMExpandImm_C(0x0ab, 1) == (0x000000ab, 1)
    assert ARMExpandImm_C(0x0ab, 0) == (0x000000ab, 0)
    assert ARMExpandImm_C(0x1ab, 1) == (0xc000002a, 1)
    assert ARMExpandImm_C(0x1ab, 0) == (0xc000002a, 1)
    assert ARMExpandImm_C(0x2ab, 1) == (0xb000000a, 1)
    assert ARMExpandImm_C(0x2ab, 0) == (0xb000000a, 1)
    assert ARMExpandImm_C(0x3ab, 1) == (0xac000002, 1)
    assert ARMExpandImm_C(0x3ab, 0) == (0xac000002, 1)
    assert ARMExpandImm_C(0x4ab, 1) == (0xab000000, 1)
    assert ARMExpandImm_C(0x4ab, 0) == (0xab000000, 1)
    for i in range(5, 16):
        assert ARMExpandImm_C(i << 8 | 0xab, 0) == (0xab << (32-2*i), 0)
        assert ARMExpandImm_C(i << 8 | 0xab, 1) == (0xab << (32-2*i), 0)
    assert ARMExpandImm(0x0ab) == 0x000000ab
    assert ARMExpandImm(0x1ab) == 0xc000002a
    assert ARMExpandImm(0x2ab) == 0xb000000a
    assert ARMExpandImm(0x3ab) == 0xac000002
    assert ARMExpandImm(0x4ab) == 0xab000000
    for i in range(5, 16):
        assert ARMExpandImm(i << 8 | 0xab) == 0xab << (32-2*i)
        
    assert AddWithCarry(0xff, 0x12, 0x34, 1) == (0x47, 0, 0)
    assert AddWithCarry(0xff, 0x12, 0x34, 0) == (0x46, 0, 0)
    assert AddWithCarry(0xff, 0x62, 0xef, 1) == (0x52, 1, 0)
    assert AddWithCarry(0xff, 0x62, 0xef, 0) == (0x51, 1, 0)
    assert AddWithCarry(0xff, 0x80, 0x7f, 1) == (0x00, 1, 0)
    assert AddWithCarry(0xff, 0x80, 0x7f, 0) == (0xff, 0, 0)
    assert AddWithCarry(0xff, 0x80, 0x80, 1) == (0x01, 1, 1)
    assert AddWithCarry(0xff, 0x80, 0x80, 0) == (0x00, 1, 1)
    assert AddWithCarry(0xff, 0x40, 0x40, 1) == (0x81, 0, 1)
    assert AddWithCarry(0xff, 0x40, 0x40, 0) == (0x80, 0, 1)

    assert ITAdvance(0b00000000) == 0
    assert ITAdvance(0b10001000) == 0
    assert ITAdvance(0b10010100) == 0b10001000
    assert ITAdvance(0b10011010) == 0b10010100
    assert ITAdvance(0b10010101) == 0b10001010


