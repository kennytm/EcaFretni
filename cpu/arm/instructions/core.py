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

from cpu.arm.instruction import Instruction, Condition
from cpu.arm.decoder import InstructionDecoder
from cpu.arm.functions import *
from bitpattern import BitPattern
from cpu.arm.operand import Register, Constant
from abc import abstractmethod
import re

#===============================================================================
# Data processing instructions
# 
#  adc, add, and, eor, sub, sbc, rsb, rsc, orr, mov (lsl, lsr, asr, ror, rrx),
#  bic, mvn, orn, pkh, movt
#
#===============================================================================

class DataProcInstruction(Instruction):
    'The base class of all data processing instructions.'
    def __init__(self, encoding, length, instructionSet, mainOpcode, targetReg, srcReg, op2, setFlags=False, append='', isADR=False):
        super().__init__(encoding, length, instructionSet)
        self.targetReg = targetReg
        self.srcReg = srcReg
        self.op2 = op2
        self.setFlags = setFlags
        self._mainOpcode = mainOpcode + append
        self.isADR = isADR

    def mainOpcode(self):
        return self._mainOpcode + ("s" if self.setFlags else "")

    @property
    def operands(self):
        return [Register(self.targetReg), Register(self.srcReg), self.op2]

    def execCoreFlagged(self, op1, op2, cpsr):
        '''The core execution method for the set-flag variant.
        
        It takes the decoded operands and the current status, and should return
        the result and modifer *cpsr* accordingly.'''
        return self.execCore(op1, op2, cpsr.C)

    @abstractmethod
    def execCore(self, op1, op2, carry):
        '''The core execution method.
        
        It takes the decoded operands and the value of carry, and should return
        the result.'''
        assert False    # pragma: no cover

    def exec(self, thread):
        cpsr = thread.cpsr
        carry = cpsr.C
        op1 = thread.r[self.srcReg]
        if self.isADR:
            op1 &= ~3 
        op2 = self.applyShift(thread, self.op2.get(thread), carry)
        targetReg = self.targetReg
        if self.setFlags:
            res = self.execCoreFlagged(op1, op2, cpsr)
            cpsr.N = res >> 31
            cpsr.Z = not res
        else:
            res = self.execCore(op1, op2, carry)
        if targetReg == REG_PC:
            (res, cpsr.T) = fixPCAddrALU(res, cpsr.T)
        thread.r[targetReg] = res

    

class ADCInstruction(DataProcInstruction):
    'The ``adc`` (add with carry) instruction.'
    def execCoreFlagged(self, op1, op2, cpsr):
        (res, carry, overflow) = AddWithCarry(0xffffffff, op1, op2, cpsr.C)
        cpsr.C = carry
        cpsr.V = overflow
        return res

    def execCore(self, op1, op2, carry):
        return (op1 + op2 + carry) & 0xffffffff

class ADDInstruction(DataProcInstruction):
    'The ``add`` (add) instruction.'
    def execCoreFlagged(self, op1, op2, cpsr):
        (res, carry, overflow) = AddWithCarry(0xffffffff, op1, op2, 0)
        cpsr.C = carry
        cpsr.V = overflow
        return res

    def execCore(self, op1, op2, carry):
        return (op1 + op2) & 0xffffffff

class ANDInstruction(DataProcInstruction):
    'The ``and`` (bitwise-AND) instruction.'
    def execCore(self, op1, op2, carry):
        return op1 & op2

class EORInstruction(DataProcInstruction):
    'The ``eor`` (bitwise-exclusive-OR) instruction.'
    def execCore(self, op1, op2, carry):
        return op1 ^ op2

class SUBInstruction(DataProcInstruction):
    'The ``sub`` (subtract) instruction.'
    def execCoreFlagged(self, op1, op2, cpsr):
        (res, carry, overflow) = AddWithCarry(0xffffffff, op1, 0xffffffff & ~op2, 1)
        cpsr.C = carry
        cpsr.V = overflow
        return res

    def execCore(self, op1, op2, carry):
        return (op1 - op2) & 0xffffffff

class SBCInstruction(DataProcInstruction):
    'The ``sbc`` (subtract with carry) instruction.'
    def execCoreFlagged(self, op1, op2, cpsr):
        (res, carry, overflow) = AddWithCarry(0xffffffff, op1, 0xffffffff & ~op2, cpsr.C)
        cpsr.C = carry
        cpsr.V = overflow
        return res

    def execCore(self, op1, op2, carry):
        return (op1 + ~op2 + carry) & 0xffffffff

class RSBInstruction(DataProcInstruction):
    'The ``rsb`` (reverse subtract) instruction.'
    def execCoreFlagged(self, op1, op2, cpsr):
        (res, carry, overflow) = AddWithCarry(0xffffffff, 0xffffffff & ~op1, op2, 1)
        cpsr.C = carry
        cpsr.V = overflow
        return res

    def execCore(self, op1, op2, carry):
        return (op2 - op1) & 0xffffffff

class RSCInstruction(DataProcInstruction):
    'The ``rsc`` (reverse subtract with carry) instruction.'
    def execCoreFlagged(self, op1, op2, cpsr):
        (res, carry, overflow) = AddWithCarry(0xffffffff, 0xffffffff & ~op1, op2, cpsr.C)
        cpsr.C = carry
        cpsr.V = overflow
        return res

    def execCore(self, op1, op2, carry):
        return (~op1 + op2 + carry) & 0xffffffff

class ORRInstruction(DataProcInstruction):
    'The ``orr`` (bitwise OR) instruction.'
    def execCore(self, op1, op2, carry):
        return op1 | op2

class ORNInstruction(DataProcInstruction):
    'The ``orn`` (bitwise OR NOT) instruction.'
    def execCore(self, op1, op2, carry):
        return (op1 | ~op2) & 0xffffffff

_shift_names = ('lsl', 'lsr', 'asr', 'ror', 'rrx')
_mov_renamer = re.compile(r'^mov([^ ]*\t[^ ]+ [^ ]+), (ls[lr]|asr|ror|rrx) ([^ ]+)$').sub

class MOVInstruction(DataProcInstruction):
    '''The ``mov`` (move), ``lsl`` (logical shift left), ``lsr`` (logical shift
    right), ``asr`` (arithmetic shift right), ``ror`` (rotate right) and ``rrx``
    (rotate right with extend) instructions.'''
    def execCore(self, op1, op2, carry):    # pragma: no cover
        return op2

    def exec(self, thread):
        cpsr = thread.cpsr
        res = self.applyShift(thread, self.op2.get(thread), cpsr.C)
        targetReg = self.targetReg
        if self.setFlags:
            cpsr.N = res >> 31
            cpsr.Z = not res
        if targetReg == REG_PC:
            (res, cpsr.T) = fixPCAddrALU(res, cpsr.T)
        thread.r[targetReg] = res

    @property
    def operands(self):
        return [Register(self.targetReg), self.op2]
    
    def __str__(self):
        return _mov_renamer(r'\2\1, \3', super().__str__())



class BICInstruction(DataProcInstruction):
    'The ``bic`` (bitwise bit clear) instruction.'
    def execCore(self, op1, op2, carry):
        return op1 & ~op2

class MVNInstruction(DataProcInstruction):
    'The ``mvn`` (bitwise NOT) instruction.'
    @property
    def operands(self):
        return [Register(self.targetReg), self.op2]
    
    def execCore(self, op1, op2, carry):    # pragma: no cover
        return 0xffffffff & ~op2
    
    def exec(self, thread):
        cpsr = thread.cpsr
        op2 = self.applyShift(thread, self.op2.get(thread), cpsr.C)
        targetReg = self.targetReg
        res = 0xffffffff & ~op2
        if self.setFlags:
            cpsr.N = res >> 31
            cpsr.Z = not res
        if targetReg == REG_PC:
            (res, cpsr.T) = fixPCAddrALU(res, cpsr.T)
        thread.r[targetReg] = res

class MOVTInstruction(DataProcInstruction):
    'The ``movt`` (move top) instruction.'
    @property
    def operands(self):
        return [Register(self.targetReg), self.op2]
    
    def execCore(self, op1, op2, carry):    # pragma: no cover
        return (op1 & 0xffff) + (op2 * 0x10000)
    

class PKHInstruction(DataProcInstruction):
    'The ``pkh`` (pack halfword) instruction.'
    def execCore(self, op1, op2, carry):
        tbform = self.shiftType
        loWord = (op2 if tbform else op1) & 0x0000ffff
        hiWord = (op1 if tbform else op2) & 0xffff0000
        return loWord + hiWord
        
    def mainOpcode(self):
        return 'pkhtb' if self.shiftType else 'pkhbt'

    def __str__(self):
        return super().__str__().replace(', asr #32', '')


#===============================================================================
# Comparing instructions
# 
#  tst, teq, cmp, cmn
#
#===============================================================================

class ComparingInstruction(Instruction):
    'The base class of all comparing instructions.'
    def __init__(self, encoding, length, instructionSet, mainOpcode, targetReg, srcReg, op2, setFlags=True, append='', isADR=False):
        super().__init__(encoding, length, instructionSet)
        self.srcReg = srcReg
        self.op2 = op2
        self._mainOpcode = mainOpcode

    def mainOpcode(self):
        return self._mainOpcode

    @property
    def operands(self):
        return [Register(self.srcReg), self.op2]

    @abstractmethod
    def execCore(self, op1, op2, cpsr):
        '''The core execution method.
        
        It takes the decoded operands and the current status, and should return
        the comparison result and modifer *cpsr* accordingly.'''
        assert False    # pragma: no cover

    def exec(self, thread):
        cpsr = thread.cpsr
        carry = cpsr.C
        op1 = thread.r[self.srcReg]
        op2 = self.applyShift(thread, self.op2.get(thread), carry)
        res = self.execCore(op1, op2, cpsr)
        cpsr.N = res >> 31
        cpsr.Z = not res

class TSTInstruction(ComparingInstruction):
    'The ``tst`` (test) instruction.'
    def execCore(self, op1, op2, cpsr):
        return op1 & op2

class TEQInstruction(ComparingInstruction):
    'The ``teq`` (test equivalence) instruction.'
    def execCore(self, op1, op2, cpsr):
        return op1 ^ op2

class CMPInstruction(ComparingInstruction):
    'The ``cmp`` (compare) instruction.'
    def execCore(self, op1, op2, cpsr):
        (res, carry, overflow) = AddWithCarry(0xffffffff, op1, 0xffffffff & ~op2, 1)
        cpsr.C = carry
        cpsr.V = overflow
        return res

class CMNInstruction(ComparingInstruction):
    'The ``cmn`` (compare negative) instruction.'
    def execCore(self, op1, op2, cpsr):
        (res, carry, overflow) = AddWithCarry(0xffffffff, op1, op2, 0)
        cpsr.C = carry
        cpsr.V = overflow
        return res

#===============================================================================
# If-then and hints instructions
# 
#  it, nop, yield, wfe, wfi, sev
#
#===============================================================================

class HintInstruction(Instruction):
    '''The ``nop`` (no operation), ``yield``, ``wfe`` (wait for event), ``wfi``
    (wait for interrupt) and ``sev`` (send event) hint instructions. In this
    emulator, all these 5 instructions considered the same as no-op.'''
    def __init__(self, encoding, length, instructionSet, mainOpcode):
        super().__init__(encoding, length, instructionSet)
        self._mainOpcode = mainOpcode
    
    @property
    def operands(self):
        return []

    def mainOpcode(self):
        return self._mainOpcode

    def exec(self, thread):
        pass

_it_opcodes = (    # for firstcond[0] == 1
    '',
    'iteee',    # nnn1
    'itee',     # nn10
    'iteet',    # nny1
    'ite',      # n100
    'itete',    # nyn1
    'itet',     # ny10
    'itett',    # nyy1
    'it',       # 1000
    'ittee',    # ynn1
    'itte',     # yn10
    'ittet',    # yny1
    'itt',      # y100
    'ittte',    # yyn1
    'ittt',     # yy10
    'itttt',    # yyy1
)
# _it_opcodes_for_firstcond[0]=0[i] = _it_opcodes[16-i]


class ITInstruction(Instruction):
    'The ``it`` (if-then) instruction.'
    def exec(self, thread):
        thread.cpsr.IT = self.itState
    
    def __init__(self, encoding, length, instructionSet, cond, mask):
        super().__init__(encoding, length, instructionSet)
    
        self.itState = cond * 16 + mask
        self._operands = [Condition(cond)]
    
        opcodeIndex = mask if cond & 1 else 16 - mask
        self._mainOpcode = _it_opcodes[opcodeIndex]
    
    @property
    def operands(self):
        return self._operands
    
    def mainOpcode(self):
        return self._mainOpcode
        

#===============================================================================
# Data processing instruction decoders
# 
#  adc, add, and, eor, sub, sbc, rsb, rsc, orr, mov (lsl, lsr, asr, ror, rrx),
#  bic, mvn, tst, teq, cmp, cmn, orn, pkh, movt
#
#===============================================================================

(_DPTYPE_AND, _DPTYPE_EOR, _DPTYPE_SUB, _DPTYPE_RSB,
 _DPTYPE_ADD, _DPTYPE_ADC, _DPTYPE_SBC, _DPTYPE_RSC,
 _DPTYPE_TST, _DPTYPE_TEQ, _DPTYPE_CMP, _DPTYPE_CMN,
 _DPTYPE_ORR, _DPTYPE_MOV, _DPTYPE_BIC, _DPTYPE_MVN,
 _DPTYPE_ORN, _DPTYPE_PKH, _DPTYPE_MOVT) = range(19)

_dataProcReg_arm_opcodes = (
    'and', 'eor', 'sub', 'rsb',
    'add', 'adc', 'sbc', 'rsc',
    'tst', 'teq', 'cmp', 'cmn',
    'orr', 'mov', 'bic', 'mvn',
    'orn', 'pkh', 'movt', '',
)
_dataProcReg_arm_classes = (
    ANDInstruction, EORInstruction, SUBInstruction, RSBInstruction,
    ADDInstruction, ADCInstruction, SBCInstruction, RSCInstruction,
    TSTInstruction, TEQInstruction, CMPInstruction, CMNInstruction,
    ORRInstruction, MOVInstruction, BICInstruction, MVNInstruction,
    ORNInstruction, PKHInstruction, MOVTInstruction, None, None)

_dataProcReg_thumb32_to_arm = {
    0: _DPTYPE_AND, 1: _DPTYPE_BIC, 2: _DPTYPE_ORR, 3: _DPTYPE_ORN,
    4: _DPTYPE_EOR, 6: _DPTYPE_PKH, 8: _DPTYPE_ADD, 10: _DPTYPE_ADC,
    11: _DPTYPE_SBC, 13: _DPTYPE_SUB, 14: _DPTYPE_RSB
}
_dataProcReg_thumb32_npc_to_arm = {
    2: _DPTYPE_MOV, 3: _DPTYPE_MVN
}
_dataProcReg_thumb32_dpc_to_arm = {
    0: _DPTYPE_TST, 4: _DPTYPE_TEQ, 8: _DPTYPE_CMN, 13: _DPTYPE_CMP
}

_dataProcReg_thumb16_is_shift = {
    2: SRTYPE_LSL, 3: SRTYPE_LSR, 4: SRTYPE_ASR, 7: SRTYPE_ROR
}


def createDataProcessingInstruction(encoding, length, instrSet, x, targetReg, srcReg, op2, setFlags=False, shiftTnA=None, isADR=False, append=''):
    'Create a data processing instruction with a given opcode type *x*.'
    mainOpcode = _dataProcReg_arm_opcodes[x]
    instrCls = _dataProcReg_arm_classes[x]
    instr = instrCls(encoding, length, instrSet, mainOpcode, targetReg, srcReg, op2, setFlags, isADR=isADR, append=append)
    if shiftTnA:
        instr.setShift(shiftTnA)
    return instr

def getARMTypeFromThumbType(xt, d, n):
    if d == REG_PC and xt in _dataProcReg_thumb32_dpc_to_arm:
        return _dataProcReg_thumb32_dpc_to_arm[xt]
    if n == REG_PC and xt in _dataProcReg_thumb32_npc_to_arm:
        return _dataProcReg_thumb32_npc_to_arm[xt]
    elif xt in _dataProcReg_thumb32_to_arm:
        return _dataProcReg_thumb32_to_arm[xt]
    else:
        return -1

# Sect A5.2.1
@InstructionDecoder(4, 0, '000xxxxSnnnnddddiiiiitt0mmmm')
def dataProcessingInstructionDecoder_ARMRegister(res, encoding, conditional):
    'Decode ARM data-processing instructions of the type ``add r0, r1, r2, lsl #3``.'
    x = res.x
    if (x & 0b1100) == 0b1000 and not res.S:
        return None
    shiftTnA = DecodeImmShift(res.t, res.i)
    op2 = Register(res.m)
    return createDataProcessingInstruction(encoding, 4, 0, x, res.d, res.n, op2, res.S, shiftTnA)

# Sect A5.2.2
@InstructionDecoder(4, 0, '000xxxxSnnnnddddssss0tt1mmmm')
def dataProcessingInstructionDecoder_ARMRegisterShiftRegister(res, encoding, conditional):
    'Decode ARM data-processing instructions of the type ``add r0, r1, r2, lsl r3``.'
    x = res.x
    if (x & 0b1100) == 0b1000 and not res.S:
        return None
    shiftTnA = (res.t, Register(res.s))
    op2 = Register(res.m)
    return createDataProcessingInstruction(encoding, 4, 0, x, res.d, res.n, op2, res.S, shiftTnA)

# Sect A5.2.3
@InstructionDecoder(4, 0, '001xxxxSnnnnddddiiiiiiiiiiii')
def dataProcessingInstructionDecoder_ARMImmediate(res, encoding, conditional):
    'Decode ARM data-processing instructions of the type ``add r0, r1, #0x2``.'
    x = res.x
    if (x & 0b1100) == 0b1000 and not res.S:
        return None
    isADR = res.n == REG_PC and x in (_DPTYPE_ADD, _DPTYPE_SUB)
    op2 = Constant(ARMExpandImm(res.i))
    return createDataProcessingInstruction(encoding, 4, 0, x, res.d, res.n, op2, res.S, isADR=isADR)

# Sect A6.2.1
@InstructionDecoder(2, 1, '000ttiiiiimmmddd')
def dataProcessingInstructionDecoder_Thumb16ShiftImmediate(res, encoding, condition):
    'Decode 16-bit Thumb ``lsl``, ``lsr`` and ``asr`` instructions of the type ``lsls r0, r1, #2``.'
    shiftType = res.t
    if shiftType == 0b11:   # ror is not part of Thumb16
        return None
    shiftTnA = DecodeImmShift(shiftType, res.i)
    op2 = Register(res.m)
    setFlags = condition == COND_NONE
    return createDataProcessingInstruction(encoding, 2, 1, _DPTYPE_MOV, res.d, res.d, op2, setFlags, shiftTnA)
    

# Sect A6.2.1
@InstructionDecoder(2, 1, '000110xmmmnnnddd')
def dataProcessingInstructionDecoder_Thumb16AddSubRegister(res, encoding, condition):
    'Decode 16-bit Thumb ``add`` and ``sub`` instructions of the type ``add r0, r1, r2``.'
    x = _DPTYPE_SUB if res.x else _DPTYPE_ADD
    setFlags = condition == COND_NONE
    op2 = Register(res.m)
    return createDataProcessingInstruction(encoding, 2, 1, x, res.d, res.n, op2, setFlags)

# Sect A6.2.1
@InstructionDecoder(2, 1, '000111xiiinnnddd')
def dataProcessingInstructionDecoder_Thumb16AddSub3BitImmediate(res, encoding, condition):
    'Decode 16-bit Thumb ``add`` and ``sub`` instructions of the type ``add r0, r1, #0x2``.'
    x = _DPTYPE_SUB if res.x else _DPTYPE_ADD
    setFlags = condition == COND_NONE
    op2 = Constant(res.i)
    return createDataProcessingInstruction(encoding, 2, 1, x, res.d, res.n, op2, setFlags)

# Sect A6.2.1
@InstructionDecoder(2, 1, '001xxdddiiiiiiii')
def dataProcessingInstructionDecoder_Thumb16_8BitImmediate(res, encoding, condition):
    'Decode 16-bit Thumb ``mov``, ``cmp``, ``add`` and ``sub`` instructions of the type ``mov r0, #0x12``.'
    x = (_DPTYPE_MOV, _DPTYPE_CMP, _DPTYPE_ADD, _DPTYPE_SUB)[res.x]
    setFlags = condition == COND_NONE
    op2 = Constant(res.i)
    return createDataProcessingInstruction(encoding, 2, 1, x, res.d, res.d, op2, setFlags)

# Sect A6.2.2
@InstructionDecoder(2, 1, '010000xxxxmmmddd')
def dataProcessingInstructionDecoder_Thumb16Register(res, encoding, condition):
    x = res.x
    shiftTnA = None
    srcReg = res.d
    if x in _dataProcReg_thumb16_is_shift:
        shiftTnA = (_dataProcReg_thumb16_is_shift[x], Register(res.m))
        op2 = Register(res.d)
        x = _DPTYPE_MOV
    elif x == 0b1001:
        srcReg = res.m
        op2 = Constant(0)
        x = _DPTYPE_RSB
    elif x == 0b1101:
        # TODO: MUL instruction
        return None
    else:
        op2 = Register(res.m)
    setFlags = condition == COND_NONE
    return createDataProcessingInstruction(encoding, 2, 1, x, res.d, srcReg, op2, setFlags, shiftTnA)

# Sect A6.2.3
@InstructionDecoder(2, 1, '010001xxdmmmmddd')
def dataProcessingInstructionDecoder_Thumb16HighRegister(res, encoding, condition):
    'Decode 16-bit Thumb ``add``, ``cmp`` and ``mov`` instructions of the type ``add r10, r11``.'
    xt = res.x
    if xt == 0b11:
        # these are B and BX instructions
        return None
    x = (_DPTYPE_ADD, _DPTYPE_CMP, _DPTYPE_MOV)[xt]
    op2 = Register(res.m)
    return createDataProcessingInstruction(encoding, 2, 1, x, res.d, res.d, op2)

# Sect A6.2.5
@InstructionDecoder(2, 1, '10110000xiiiiiii')
def dataProcessingInstructionDecoder_Thumb16AddSubSP(res, encoding, condition):
    'Decode 16-bit Thumb ``add`` or ``sub`` instructions of the type ``add sp, sp, #1``.'
    x = _DPTYPE_SUB if res.x else _DPTYPE_ADD
    op2 = Constant(res.i * 4)
    return createDataProcessingInstruction(encoding, 2, 1, x, REG_SP, REG_SP, op2)

# Sect A8.6.8
@InstructionDecoder(2, 1, '10101dddiiiiiiii')
def dataProcessingInstructionDecoder_Thumb16AddSP(res, encoding, condition):
    'Decode 16-bit Thumb ``add`` instruction of the type ``add rd, sp, #1``.'
    op2 = Constant(res.i * 4)
    return createDataProcessingInstruction(encoding, 2, 1, _DPTYPE_ADD, res.d, REG_SP, op2)

# Sect A6.3.1
@InstructionDecoder(4, 1, '11110i0xxxxSnnnn 0iiiddddiiiiiiii')
def dataProcessingInstructionDecoder_Thumb32Immediate(res, encoding, condition):
    'Decode 32-bit Thumb data-processing instructions of the type ``add.w r0, r1, #0x23``.'
    x = getARMTypeFromThumbType(res.x, res.d, res.n)
    if x < 0 or x == _DPTYPE_PKH:
        return None
    op2 = Constant(ThumbExpandImm(res.i))
    return createDataProcessingInstruction(encoding, 4, 1, x, res.d, res.n, op2, res.S).forceWide()

# Sect A6.3.3
@InstructionDecoder(4, 1, '11110i10x0x0nnnn 0iiiddddiiiiiiii')
def dataProcessingInstructionDecoder_Thumb32ImmediateW(res, encoding, condition):
    'Decode 32-bit Thumb data-processing instructions of the type ``addw r0, r1, #0x23``.'
    xt = res.x
    if xt == 0:
        x = _DPTYPE_ADD
    elif xt == 3:
        x = _DPTYPE_SUB
    else:
        return None
    op2 = Constant(res.i)
    isADR = res.n == REG_PC
    return createDataProcessingInstruction(encoding, 4, 1, x, res.d, res.n, op2, isADR=isADR, append='w')

# Sect A6.3.11
@InstructionDecoder(4, 1, '1110101xxxxSnnnn 0iiiddddiittmmmm')
def dataProcessingInstructionDecoder_Thumb32Register(res, encoding, condition):
    'Decode 32-bit Thumb data-processing instructions of the type ``add.w r0, r1, r2, lsl #3``.'
    x = getARMTypeFromThumbType(res.x, res.d, res.n)
    if x < 0:
        return None
    op2 = Register(res.m)
    shiftTnA = DecodeImmShift(res.t, res.i)
    return createDataProcessingInstruction(encoding, 4, 1, x, res.d, res.n, op2, res.S, shiftTnA).forceWide()

# Sect A6.3.12
@InstructionDecoder(4, 1, '111110100ttSnnnn 1111dddd0000mmmm')
def dataProcessingInstructionDecoder_Thumb32RegisterShiftInstr(res, encoding, condition):
    'Decode 32-bit Thumb shift instructions of the type ``lsl.w r0, r1, r2``.'
    op2 = Register(res.n)
    shiftTnA = (res.t, Register(res.m))
    return createDataProcessingInstruction(encoding, 4, 1, _DPTYPE_MOV, res.d, res.d, op2, res.S, shiftTnA).forceWide()

# Sect A8.6.10
@InstructionDecoder(2, 1, '10100dddiiiiiiii')
def ADRInstructionDecoder_Thumb16(res, encoding, condition):
    op2 = Constant(res.i * 4)
    return createDataProcessingInstruction(encoding, 2, 1, _DPTYPE_ADD, res.d, REG_PC, op2, isADR=True)

# Sect A5.2
@InstructionDecoder(4, 0, '00110x00iiiiddddiiiiiiiiiiii')
def specialMoveInstructionDecoder_ARM(res, encoding, condition):
    if res.x:
        x = _DPTYPE_MOVT
        append = ''
    else:
        x = _DPTYPE_MOV
        append = 'w'
    op2 = Constant(res.i)
    return createDataProcessingInstruction(encoding, 4, 0, x, res.d, res.d, op2, append=append)

# Sect A6.3.3
@InstructionDecoder(4, 1, '11110i10x100IIII 0iiiddddiiiiiiii')
def specialMoveInstructionDecoder_Thumb32(res, encoding, condition):
    if res.x:
        x = _DPTYPE_MOVT
        append = ''
    else:
        x = _DPTYPE_MOV
        append = 'w'
    op2 = Constant(res.i + res.I * 0x1000)
    return createDataProcessingInstruction(encoding, 4, 1, x, res.d, res.d, op2, append=append)

#===============================================================================
# If-then and hints instruction decoder
# 
#  it, nop, yield, wfe, wfi, sev
#
#===============================================================================

_hint_opcodes = ('nop', 'yield', 'wfe', 'wfi', 'sev')

@InstructionDecoder(4, 0, '0011001000001111000000000xxx')
def hintInstructionDecoder_ARM(res, encoding, condition):
    x = res.x
    if x > 4:
        return None
    return HintInstruction(encoding, 4, 0, _hint_opcodes[x])

@InstructionDecoder(2, 1, '101111110xxx0000')
def hintInstructionDecoder_Thumb16(res, encoding, condition):
    x = res.x
    if x > 4:
        return None
    return HintInstruction(encoding, 2, 1, _hint_opcodes[x])

@InstructionDecoder(4, 1, '1111001110101111 1000000000000xxx')
def hintInstructionDecoder_Thumb32(res, encoding, condition):
    x = res.x
    if x > 4:
        return None
    return HintInstruction(encoding, 4, 1, _hint_opcodes[x]).forceWide()

@InstructionDecoder(2, 1, '10111111ccccmmmm')
def ITInstructionDecoder_Thumb16(res, encoding, condition):
    m = res.m
    if not m:
        return None
    return ITInstruction(encoding, 2, 1, res.c, m)
