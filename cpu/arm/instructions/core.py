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
    

_adc_thumb32_imm = BitPattern('11110i01010Snnnn0iiiddddiiiiiiii').unpack
_adc_arm_imm = BitPattern('0010101Snnnnddddiiiiiiiiiiii').unpack
_adc_thumb16_reg = BitPattern('0100000101mmmddd').unpack
_adc_thumb32_reg = BitPattern('11101011010Snnnn0iiiddddiittmmmm').unpack
_adc_arm_reg = BitPattern('0000101Snnnnddddiiiiitt0mmmm').unpack
_adc_arm_shiftreg = BitPattern('0000101Snnnnddddssss0tt1mmmm').unpack

class ADCInstruction(Instruction):
    'The "Add with carry" (adc) instruction.'
    
    def __init__(self, encoding, length, instructionSet, targetReg, srcReg, op2, setFlags):
        super().__init__(encoding, length, instructionSet)
        self.targetReg = targetReg
        self.srcReg = srcReg
        self.op2 = op2
        self.setFlags = setFlags
    
    @classmethod
    def tryCreate(cls, enc, ln, inS, cond):
        if inS & 1:
            if ln == 2:
                res = _adc_thumb16_reg(enc)
                if res:
                    return ADCInstruction(enc, ln, inS, res.d, res.d, Register(res.m), cond == 15)
            else:
                res = _adc_thumb32_imm(enc)
                if res:
                    imm = ThumbExpandImm(res.i)
                    return ADCInstruction(enc, ln, inS, res.d, res.n, Constant(imm), res.S)
                res = _adc_thumb32_reg(enc)
                if res:
                    shiftTnA = DecodeImmShift(res.t, res.i)
                    return ADCInstruction(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA).forceWide()
        else:
            res = _adc_arm_imm(enc)
            if res:
                imm = ARMExpandImm(res.i)
                return ADCInstruction(enc, ln, inS, res.d, res.n, Constant(imm), res.S)
            res = _adc_arm_reg(enc)
            if res:
                shiftTnA = DecodeImmShift(res.t, res.i)
                return ADCInstruction(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA)
            res = _adc_arm_shiftreg(enc)
            if res:
                shiftTnA = (res.t, Register(res.s))
                return ADCInstruction(enc, ln, inS, res.d, res.n, Register(res.m), res.S).setShift(shiftTnA)
        return None
        
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
            (res, cpsr.T) = fixPCAddrBX(res)
        thread.r[targetReg] = res


