#    
#    core.py ... The core instructions
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

from cpu.arm.instruction import Instruction
from cpu.arm.functions import *
from bitpattern import BitPattern
from cpu.arm.operand import Register, Constant

__all__ = ['ADCInstruction', 'ADDInstruction']
    

_adc_thumb32_imm  = BitPattern('11110i01010Snnnn 0iiiddddiiiiiiii').unpack
_adc_arm_imm      = BitPattern('0010101Snnnnddddiiiiiiiiiiii').unpack
_adc_thumb16_reg  = BitPattern('0100000101mmmddd').unpack
_adc_thumb32_reg  = BitPattern('11101011010Snnnn 0iiiddddiittmmmm').unpack
_adc_arm_reg      = BitPattern('0000101Snnnnddddiiiiitt0mmmm').unpack
_adc_arm_shiftreg = BitPattern('0000101Snnnnddddssss0tt1mmmm').unpack

class ADCInstruction(Instruction):
    'The ``adc`` (add with carry) instruction.'
    
    def __init__(self, encoding, length, instructionSet, targetReg, srcReg, op2, setFlags):
        super().__init__(encoding, length, instructionSet)
        self.targetReg = targetReg
        self.srcReg = srcReg
        self.op2 = op2
        self.setFlags = setFlags
    
    # enc = encoding,          ln = length of instruction in bytes,
    # inS = instruction set, cond = condition code
    @classmethod
    def tryCreate(cls, enc, ln, inS, cond):
        if inS & 1:
            if ln == 2:
                res = _adc_thumb16_reg(enc)
                if res:
                    return cls(enc, ln, inS, res.d, res.d, Register(res.m), cond == 15)
            else:
                res = _adc_thumb32_imm(enc)
                if res:
                    imm = ThumbExpandImm(res.i)
                    return cls(enc, ln, inS, res.d, res.n, Constant(imm), res.S).forceWide()
                res = _adc_thumb32_reg(enc)
                if res:
                    shiftTnA = DecodeImmShift(res.t, res.i)
                    return cls(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA).forceWide()
        else:
            res = _adc_arm_imm(enc)
            if res:
                imm = ARMExpandImm(res.i)
                return cls(enc, ln, inS, res.d, res.n, Constant(imm), res.S)
            res = _adc_arm_reg(enc)
            if res:
                shiftTnA = DecodeImmShift(res.t, res.i)
                return cls(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA)
            res = _adc_arm_shiftreg(enc)
            if res:
                shiftTnA = (res.t, Register(res.s))
                return cls(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA)
        
    def mainOpcode(self):
        return "adc" + ("s" if self.setFlags else "")
    
    @property
    def operands(self):
        return [Register(self.targetReg), Register(self.srcReg), self.op2]
    
    def exec(self, thread):
        cpsr = thread.cpsr
        origCarry = cpsr.C
        op1 = thread.r[self.srcReg]
        op2 = self.applyShift(thread, self.op2.get(thread), origCarry)
        targetReg = self.targetReg
        if self.setFlags:
            (res, carry, overflow) = AddWithCarry(0xffffffff, op1, op2, origCarry)
            cpsr.C = carry
            cpsr.V = overflow
            cpsr.N = res >> 31
            cpsr.Z = not res
        else:
            res = (op1 + op2 + origCarry) & 0xffffffff
        if targetReg == 15:
            (res, cpsr.T) = fixPCAddrALU(res)
        thread.r[targetReg] = res




_add_thumb16_imm3 = BitPattern('0001110iiinnnddd').unpack
_add_thumb16_imm8 = BitPattern('00110dddiiiiiiii').unpack
_add_thumb32_imm  = BitPattern('11110i01000Snnnn 0iiiddddiiiiiiii').unpack
_add_thumb32_immW = BitPattern('11110i100000nnnn 0iiiddddiiiiiiii').unpack
_add_arm_imm      = BitPattern('0010100Snnnnddddiiiiiiiiiiii').unpack
_add_thumb16_reg  = BitPattern('0001100mmmnnnddd').unpack
_add_thumb16_regH = BitPattern('01000100dmmmmddd').unpack
_add_thumb32_reg  = BitPattern('11101011000Snnnn 0iiiddddiittmmmm').unpack
_add_arm_reg      = BitPattern('0000100Snnnnddddiiiiitt0mmmm').unpack
_add_arm_shiftreg = BitPattern('0000100Snnnnddddssss0tt1mmmm').unpack

_adr_thumb16_add  = BitPattern('10100dddiiiiiiii').unpack
_adr_thumb32_add  = BitPattern('11110i1000001111 0iiiddddiiiiiiii').unpack
_adr_thumb32_sub  = BitPattern('11110i1010101111 0iiiddddiiiiiiii').unpack
_adr_arm_sub      = BitPattern('001001001111ddddiiiiiiiiiiii').unpack
_adr_arm_add      = BitPattern('001010001111ddddiiiiiiiiiiii').unpack

class ADDInstruction(Instruction):
    '''The ``add`` (add) instruction, and the ``adr`` (form pc-relative address)
    instruction with positive offset.'''

    def __init__(self, encoding, length, instructionSet, targetReg, srcReg, op2, setFlags=False, mainOpcode='add'):
        super().__init__(encoding, length, instructionSet)
        self.targetReg = targetReg
        self.srcReg = srcReg
        self.op2 = op2
        self.setFlags = setFlags
        self._mainOpcode = mainOpcode

    @classmethod
    def tryCreate(cls, enc, ln, inS, cond):
        if inS & 1:
            if ln == 2:
                res = _add_thumb16_imm3(enc)
                if res:
                    return cls(enc, ln, inS, res.d, res.n, Constant(res.i), cond==15 and res.d != 14)
                res = _add_thumb16_imm8(enc)
                if res:
                    return cls(enc, ln, inS, res.d, res.d, Constant(res.i), cond==15 and res.d != 14)
                res = _add_thumb16_reg(enc)
                if res:
                    return cls(enc, ln, inS, res.d, res.n, Register(res.m), cond==15 and res.d != 14)
                res = _add_thumb16_regH(enc)
                if res:
                    return cls(enc, ln, inS, res.d, res.d, Register(res.m), False) 
                res = _adr_thumb16_add(enc)
                if res:
                    return cls(enc, ln, inS, res.d, 15, Constant(4 * res.i), False)
                res = _adr_thumb32_add(enc)
                if res:
                    return cls(enc, ln, inS, res.d, 15, Constant(res.i), False).forceWide()
            else:
                res = _add_thumb32_imm(enc)
                if res:
                    if res.d == 15 and res.S:
                        return None
                    imm32 = ThumbExpandImm(res.i)
                    return cls(enc, ln, inS, res.d, res.n, Constant(imm), res.S).forceWide()
                res = _add_thumb32_immW(enc)
                if res:
                    return cls(enc, ln, inS, res.d, res.n, Constant(res.i), mainOpcode='addw')
                res = _add_thumb32_reg(enc)
                if res:
                    if res.d == 15 and res.S:
                        return None
                    shiftTnA = DecodeImmShift(res.t, res.i)
                    return cls(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA).forceWide()
        else:
            res = _add_arm_imm(enc)
            if res:
                imm = ARMExpandImm(res.i)
                return cls(enc, ln, inS, res.d, res.n, Constant(imm), res.S)
            res = _add_arm_reg(enc)
            if res:
                shiftTnA = DecodeImmShift(res.t, res.i)
                return cls(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA)
            res = _add_arm_shiftreg(enc)
            if res:
                shiftTnA = (res.t, Register(res.s))
                return cls(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA)
            
    def mainOpcode(self):
        return self._mainOpcode + ("s" if self.setFlags else "")

    @property
    def operands(self):
        return [Register(self.targetReg), Register(self.srcReg), self.op2]

    def exec(self, thread):
        cpsr = thread.cpsr
        op1 = thread.r[self.srcReg]
        op2 = self.applyShift(thread, self.op2.get(thread), cpsr.C)
        targetReg = self.targetReg
        if self.setFlags:
            (res, carry, overflow) = AddWithCarry(0xffffffff, op1, op2, 0)
            cpsr.C = carry
            cpsr.V = overflow
            cpsr.N = res >> 31
            cpsr.Z = not res
        else:
            res = (op1 + op2) & 0xffffffff
        if targetReg == 15:
            (res, cpsr.T) = fixPCAddrALU(res)
        thread.r[targetReg] = res





