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
from cpu.arm.operand import Register, Constant, PCRelative, Indirect, RegisterList
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
# Branch instructions
# 
#  b, bl, bx, blx
#
#===============================================================================

def isBLInstruction(instruction):
    'Check if *instruction* is a ``bl`` or ``blx`` instruction.'
    if isinstance(instruction, BLInstruction):
        return True
    elif isinstance(instruction, BXInstruction):
        return instruction.link
    else:
        return False
    

class BInstruction(Instruction):
    'The ``b`` (branch) instruction.'
    def __init__(self, encoding, length, instructionSet, target):
        super().__init__(encoding, length, instructionSet)
        self.target = target
    
    @property
    def operands(self):
        return [self.target]
    
    def mainOpcode(self):
        return 'b'
    
    def exec(self, thread):
        thread.pc = fixPCAddrB(self.target.get(thread), thread.cpsr.T)

class BLInstruction(Instruction):
    '''The ``bl`` (branch with link) and ``blx`` (branch with link and exchange
    instruction set) instructions for immediate offset.'''
    def __init__(self, encoding, length, instructionSet, target, exchange=False):
        super().__init__(encoding, length, instructionSet)
        self.target = target
        self._mainOpcode = ('bl', 'blx')[exchange]
        self.toThumb = (instructionSet & 1) != exchange
    
    @property
    def operands(self):
        return [self.target]
    
    def mainOpcode(self):
        return self._mainOpcode
    
    def exec(self, thread):
        cpsr = thread.cpsr
        pc = thread.pc
        toThumb = self.toThumb
        if cpsr.T:
            thread.lr = pc | 1
        else:
            thread.lr = pc - 4
        if not toThumb:
            pc &= ~3
        cpsr.T = toThumb
        thread.pc = fixPCAddrB(self.target.delta + pc, toThumb)

class BXInstruction(Instruction):
    '''
    The ``bx`` (branch and exchange) (*instrType*=1), ``bxj`` (branch and
    exchange Jazelle) (*instrType*=2) and ``blx`` (branch with link and exchange)
    (*instrType*=3) instructions for registers.
    '''
    def __init__(self, encoding, length, instructionSet, target, instrType):
        super().__init__(encoding, length, instructionSet)
        self.target = target
        self._mainOpcode = ('', 'bx', 'bxj', 'blx')[instrType]
        self.link = instrType == 3
    
    @property
    def operands(self):
        return [self.target]
    
    def mainOpcode(self):
        return self._mainOpcode
    
    def exec(self, thread):
        cpsr = thread.cpsr
        pc = thread.pc
        if self.link:
            if cpsr.T:
                thread.lr = (pc - 2) | 1
            else:
                thread.lr = pc - 4
        (thread.pc, cpsr.T) = fixPCAddrBX(self.target.get(thread))


class CBZInstruction(Instruction):
    '''The ``cbz`` (compare and branch on zero) and ``cbnz`` (compare and branch
    on nonzero) instructions.'''
    
    def __init__(self, encoding, length, instructionSet, srcReg, target, nonzero):
        super().__init__(encoding, length, instructionSet)
        self.srcReg = srcReg
        self.target = target
        self.nonzero = nonzero
    
    @property
    def operands(self):
        return [Register(self.srcReg), self.target]
    
    def mainOpcode(self):
        return 'cbnz' if self.nonzero else 'cbz'
    
    def exec(self, thread):
        if self.nonzero == (not not thread.r[self.srcReg]):
            thread.pc = fixPCAddrB(self.target.get(thread), thread.cpsr.T)


#===============================================================================
# Load/store instructions
# 
#  ldr, str, ldrt, strt, ldrb, strb, ldrsb, strsb, ldrh, strh, ldrsh, strsh,
#  ldrbt, strbt, ldrht, strht, ldrd, strd, ldrex, strex, ldrexb, strexb,
#  ldrexh, strexh, ldrexd, strexd
#
#===============================================================================

class LDRInstruction(Instruction):
    'The ``ldr`` (load register)-related instructions.'
    def __init__(self, encoding, length, instructionSet, targetReg, op, append='', loadLen=4, align=~0, signedNotMask=0):
        super().__init__(encoding, length, instructionSet)
        self.targetReg = targetReg
        self.op = op
        self.loadLen = loadLen
        self.align = align
        self._mainOpcode = 'ldr' + append
        self.signedNotMask = signedNotMask
    
    @property
    def operands(self):
        return [Register(self.targetReg), self.op]
    
    def mainOpcode(self):
        return self._mainOpcode
    
    def exec(self, thread):
        val = self.op.get(thread, self.loadLen, self.align)
        t = self.targetReg
        if t == REG_PC:
            (val, thread.cpsr.T) = fixPCAddrLoad(val, thread.cpsr.T)
        snm = self.signedNotMask
        if snm:
            val = 0xffffffff & signed(snm, val)
        thread.r[t] = val

class STRInstruction(Instruction):
    'The ``str`` (store register)-related instructions.'
    def __init__(self, encoding, length, instructionSet, srcReg, op, append='', loadLen=4, align=~0, signedNotMask=0):
        super().__init__(encoding, length, instructionSet)
        self.srcReg = srcReg
        self.op = op
        self.loadLen = loadLen
        self._mainOpcode = 'str' + append
    
    @property
    def operands(self):
        return [Register(self.srcReg), self.op]
    
    def mainOpcode(self):
        return self._mainOpcode
    
    def exec(self, thread):
        self.op.set(thread, thread.r[self.srcReg], self.loadLen)

#===============================================================================
# Load/store multiple instruction decoder
# 
#  ldmXX, stmXX
#
#===============================================================================

def _getLoadStoreMultipleInfo(startAddress, offset, isInc, before):
    # ldmia:                        ldmib:
    #     sp+c <--------- new sp        sp+c ==> r2 <-- new sp
    #     sp+8 ==> r2                   sp+8 ==> r1
    #     sp+4 ==> r1                   sp+4 ==> r0
    #     sp   ==> r0                   sp
    # 
    # ldmda:                        ldmdb:
    #     sp   ==> r2                   sp
    #     sp-4 ==> r1                   sp-4 ==> r2
    #     sp-8 ==> r0                   sp-8 ==> r1
    #     sp-c <--------- new sp        sp-c ==> r0 <-- new sp
    #

    endAddress = startAddress
    if isInc:
        newAddress = startAddress + offset  # valid for ***ia
        endAddress = newAddress
    else:
        startAddress -= offset      # valid for ***db
        newAddress = startAddress
    if before == isInc:    # fix for ***ib & ***da
        startAddress += 4
        endAddress += 4
    
    addrs = []
    aa = addrs.append
    while startAddress != endAddress:
        aa(startAddress)
        startAddress += 4
    
    return (newAddress, addrs)

class LDMInstruction(Instruction):
    '''The ``ldm`` (load multiple)-related instructions, including ``pop`` (pop
    multiple registers).'''
    def __init__(self, encoding, length, instructionSet, srcReg, targetRegList, writeBack, inc, before, excMode=False):
        super().__init__(encoding, length, instructionSet)
        self.writeBack = writeBack
        self.srcReg = srcReg
        self.targetRegList = targetRegList
        self.inc = inc
        self.before = before
        self.excMode = excMode
        self.isPop = srcReg == REG_SP and writeBack and inc and not before and not excMode
    
    def mainOpcode(self):
        if self.isPop:
            return 'pop'
        else:
            return 'ldm' + ('i' if self.inc else 'd') + ('b' if self.before else 'a')
    
    @property
    def operands(self):
        return [Register(self.srcReg), self.targetRegList]
        
    def __str__(self):
        newStr = super().__str__()
        if self.isPop:
            return newStr.replace('sp, ', '', 1)
        else:
            if self.writeBack:
                newStr = newStr.replace(',', '!,', 1)
            if self.excMode:
                newStr += '^'
            return newStr
    
    def exec(self, thread):
        srcReg = self.srcReg
        rl = self.targetRegList
        offset = len(rl)*4
        
        startAddress = thread.r[srcReg]
        (newAddress, addresses) = _getLoadStoreMultipleInfo(startAddress, offset, self.inc, self.before)
        
        values = map(thread.memory.get, addresses)
        rl.set(thread, values)
        if self.writeBack:
            thread.r[srcReg] = newAddress

class STMInstruction(Instruction):
    '''The ``stm`` (store multiple)-related instructions, including ``push``
    (push multiple registers).'''
    def __init__(self, encoding, length, instructionSet, targetReg, srcRegList, writeBack, inc, before, excMode=False):
        super().__init__(encoding, length, instructionSet)
        self.writeBack = writeBack
        self.targetReg = targetReg
        self.srcRegList = srcRegList
        self.inc = inc
        self.before = before
        self.excMode = excMode
        self.isPush = targetReg == REG_SP and writeBack and not inc and before and not excMode
    
    def mainOpcode(self):
        if self.isPush:
            return 'push'
        else:
            return 'stm' + ('i' if self.inc else 'd') + ('b' if self.before else 'a')
    
    @property
    def operands(self):
        return [Register(self.targetReg), self.srcRegList]
        
    def __str__(self):
        newStr = super().__str__()
        if self.isPush:
            return newStr.replace('sp, ', '', 1)
        else:
            if self.writeBack:
                newStr = newStr.replace(',', '!,', 1)
            if self.excMode:
                newStr += '^'
            return newStr
    
    def exec(self, thread):
        targetReg = self.targetReg
        rl = self.srcRegList
        offset = len(rl)*4
        isInc = self.inc
        
        startAddress = thread.r[targetReg]
        (newAddress, addresses) = _getLoadStoreMultipleInfo(startAddress, offset, self.inc, self.before)

        values = rl.get(thread)
        tms = thread.memory.set
        for addr, val in zip(addresses, values):
            tms(addr, val)
        
        if self.writeBack:
            thread.r[targetReg] = newAddress


################################################################################
################################################################################
################################################################################


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
    'Decode 16-bit Thumb data-processing instructions of the type ``adcs r0, r0, r1``.'
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
    'Decode 16-bit Thumb ``add`` instruction of the type ``add r0, sp, #4``.'
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
@InstructionDecoder(4, 1, '1110101xxxxSnnnn _iiiddddiittmmmm')
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
    'Decode 16-bit Thumb ``adr`` instruction (a.k.a. ``add r0, pc, #4``)'
    op2 = Constant(res.i * 4)
    return createDataProcessingInstruction(encoding, 2, 1, _DPTYPE_ADD, res.d, REG_PC, op2, isADR=True)

# Sect A5.2
@InstructionDecoder(4, 0, '00110x00iiiiddddiiiiiiiiiiii')
def specialMoveInstructionDecoder_ARM(res, encoding, condition):
    'Decode ARM ``movw`` and ``movt`` instructions.'
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
    'Decode 32-bit Thumb ``movw`` and ``movt`` instructions.'
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

@InstructionDecoder(4, 0, '001100100000________00000xxx')
def hintInstructionDecoder_ARM(res, encoding, condition):
    'Decode ARM hint instructions.'
    x = res.x
    if x > 4:
        return None
    return HintInstruction(encoding, 4, 0, _hint_opcodes[x])

@InstructionDecoder(2, 1, '101111110xxx0000')
def hintInstructionDecoder_Thumb16(res, encoding, condition):
    'Decode 16-bit Thumb hint instructions.'
    x = res.x
    if x > 4:
        return None
    return HintInstruction(encoding, 2, 1, _hint_opcodes[x])

@InstructionDecoder(4, 1, '111100111010____ 10_0_00000000xxx')
def hintInstructionDecoder_Thumb32(res, encoding, condition):
    'Decode 32-bit Thumb hint instructions.'
    x = res.x
    if x > 4:
        return None
    return HintInstruction(encoding, 4, 1, _hint_opcodes[x]).forceWide()

@InstructionDecoder(2, 1, '10111111ccccmmmm')
def ITInstructionDecoder_Thumb16(res, encoding, condition):
    'Decode 16-bit Thumb ``it`` instruction.'
    m = res.m
    if not m:
        return None
    return ITInstruction(encoding, 2, 1, res.c, m)


#===============================================================================
# Branch instruction decoder
# 
#  b, bx, bl, blx
#
#===============================================================================

# Sect A5.5
@InstructionDecoder(4, 0, '101xiiiiiiiiiiiiiiiiiiiiiiii')
def branchInstructionDecoder_ARMLocal(res, encoding, condition):
    'Decode ARM ``b`` and ``bl`` instructions.'
    delta = signed(-1<<26, res.i * 4)
    instrClr = (BInstruction, BLInstruction)[res.x]
    return instrClr(encoding, 4, 0, PCRelative(delta))

# Sect A5.5
@InstructionDecoder(4, 0, '101Hiiiiiiiiiiiiiiiiiiiiiiii', unconditional=True)
def branchInstructionDecoder_ARMExchange(res, encoding, condition):
    'Decode ARM ``blx`` instruction of the type ``blx 0x4321``'
    delta = signed(-1<<26, res.i * 4 + res.H * 2)
    return BLInstruction(encoding, 4, 0, PCRelative(delta), exchange=True)

# Sect A5.2.12
@InstructionDecoder(4, 0, '00010010____________00xxmmmm')
def branchInstructionDecoder_ARMRegister(res, encoding, condition):
    'Decode ARM ``bx``, ``bxj`` and ``blx`` instructions.'
    instrType = res.x
    if not instrType:
        # msr & mrs instructions
        return None
    target = Register(res.m)
    return BXInstruction(encoding, 4, 0, target, instrType)

# Sect A6.2.6
@InstructionDecoder(2, 1, '1101cccciiiiiiii')
def branchInstructionDecoder_Thumb16Conditional(res, encoding, condition):
    'Decode 16-bit Thumb conditional ``b`` instructions.'
    cond = res.c
    if cond >= 0b1110:
        # svc
        return None
    delta = signed(-1<<9, res.i*2)
    instr = BInstruction(encoding, 2, 1, PCRelative(delta))
    instr.condition = Condition(cond)
    return instr

# Sect A8.6.16/A6.2
@InstructionDecoder(2, 1, '11100iiiiiiiiiii')
def branchInstructionDecoder_Thumb16Unconditional(res, encoding, condition):
    'Decode the 16-bit Thumb unconditional ``b`` instruction.'
    delta = signed(-1<<12, res.i*2)
    return BInstruction(encoding, 2, 1, PCRelative(delta))

# Sect A6.2.3
@InstructionDecoder(2, 1, '01000111xmmmm___')
def branchInstructionDecoder_Thumb16Register(res, encoding, condition):
    'Decode 16-bit Thumb ``bx`` and ``blx`` instructions.'
    instrType = 2 * res.x + 1
    target = Register(res.m)
    return BXInstruction(encoding, 2, 1, target, instrType)

# Sect A6.2.5/A8.6.27
@InstructionDecoder(2, 1, '1011x0i1iiiiinnn')
def branchInstructionDecoder_Thumb16CBZ(res, encoding, condition):
    'Decode 16-bit Thumb ``cbz`` and ``cbnz`` instructions.'
    return CBZInstruction(encoding, 2, 1, res.n, PCRelative(res.i*2), res.x)

# Sect A6.3.4
@InstructionDecoder(4, 1, '11110Scccciiiiii 10J0jiiiiiiiiiii')
def branchInstructionDecoder_Thumb32Conditional(res, encoding, condition):
    'Decode 32-bit Thumb conditional ``b`` instructions.'
    cond = res.c
    if cond >= 0b1110:
        return None
    delta = signed(-1<<21, res.i*2 + res.j*0x40000 + res.J*0x80000 + res.S*0x100000)
    instr = BInstruction(encoding, 4, 1, PCRelative(delta))
    instr.condition = Condition(cond)
    return instr.forceWide()

# Sect A6.3.4
@InstructionDecoder(4, 1, '11110jiiiiiiiiii 1xjxjiiiiiiiiiii')
def branchInstructionDecoder_Thumb32Unconditional(res, encoding, condition):
    'Decode 32-bit Thumb unconditional ``b``, ``bl`` and ``blx`` instructions.'
    x = res.x
    if not x:
        return None
    j = res.j
    j ^= 3*(j<4)
    delta = signed(-1<<25, res.i*2 + j*0x400000)
    target = PCRelative(delta)
    
    if x == 1:
        instr = BInstruction(encoding, 4, 1, target)
    else:
        instr = BLInstruction(encoding, 4, 1, target, exchange=(x==2))
    return instr.forceWide()

# Sect A8.6.26
@InstructionDecoder(4, 1, '111100111100mmmm 10_0____________')
def branchInstructionDecoder_Thumb32BXJ(res, encoding, condition):
    'Decode the 32-bit Thumb ``bxj`` instruction.'
    return BXInstruction(encoding, 4, 1, Register(res.m), instrType=2)

#===============================================================================
# Load/store instruction decoder
# 
#  ldr, str, ldrt, strt, ldrb, strb, ldrsb, strsb, ldrh, strh, ldrsh, strsh,
#  ldrbt, strbt, ldrht, strht, ldrd, strd, ldrex, strex, ldrexb, strexb,
#  ldrexh, strexh, ldrexd, strexd
#
#===============================================================================

# Sect A5.3
@InstructionDecoder(4, 0, '010pubwxnnnnddddiiiiiiiiiiii')
def loadStoreInstructionDecoder_ARMImmediate(res, encoding, condition):
    '''Decode ARM ``ldr``, ``str``, ``ldrt``, ``strt``, ``ldrb``, ``strb``,
    ``ldrbt`` and ``strbt`` instructions of the type ``ldr r0, [r1, #4]``'''
    # (including the literal variant...)
    n = res.n
    p = res.p
    u = res.u
    w = res.w
    isLDR = res.x
    imm12 = res.i
    instrCls = LDRInstruction if isLDR else STRInstruction
    wback = w or not p
    
    op = Indirect(Register(n), Constant(imm12), positive=u, writeBack=wback, index=p)
    if res.b:
        suffix = 'b'
        loadLen = 1
    else:
        suffix = ''
        loadLen = 4
    if w and not p:
        suffix += 't'
    align = ~3 if n == REG_PC else ~0
    
    return instrCls(encoding, 4, 0, res.d, op, suffix, loadLen, align)

# Sect A5.3
@InstructionDecoder(4, 0, '011pubwxnnnnddddiiiiitt0mmmm')
def loadStoreInstructionDecoder_ARMRegister(res, encoding, condition):
    '''Decode ARM ``ldr``, ``str``, ``ldrt``, ``strt``, ``ldrb``, ``strb``,
    ``ldrbt`` and ``strbt`` instructions of the type ``ldr r0, [r1, r2, lsl
    #3]``.'''
    p = res.p
    w = res.w
    instrCls = LDRInstruction if res.x else STRInstruction
    wback = w or not p
    (shiftType, shiftAmount) = DecodeImmShift(res.t, res.i)
    op = Indirect(Register(res.n), Register(res.m),
            positive=res.u, writeBack=wback, index=p,
            shiftType=shiftType, shiftAmount=shiftAmount)
    if res.b:
        suffix = 'b'
        loadLen = 1
    else:
        suffix = ''
        loadLen = 4
    if w and not p:
        suffix += 't'
    return instrCls(encoding, 4, 0, res.d, op, suffix, loadLen)

_loadStore_thumb16_suffix = ('', 'h', 'b', 'sb', '', 'h', 'b', 'sh')
_loadStore_thumb16_length = (4, 2, 1, 1, 4, 2, 1, 2)
_loadStore_thumb16_signedNotMask = (0, 0, 0, -1<<8, 0, 0, 0, -1<<16)
_loadStore_thumbEE_shift = (0, 1, 1, 2)

# Sect A6.2.4
@InstructionDecoder(2, 1, '0101xxxmmmnnnddd')
def loadStoreInstructionDecoder_Thumb16Register(res, encoding, condition):
    '''Decode 16-bit Thumb ``str``, ``strh``, ``strb``, ``ldrsb``, ``ldr``, 
    ``ldrh``, ``ldrb`` and ``ldrsh`` instructions of the type ``ldr r0, [r1,
    r2]``.'''
    x = res.x
    instrCls = LDRInstruction if x >= 0b11 else STRInstruction
    op = Indirect(Register(res.n), Register(res.m))
    append = _loadStore_thumb16_suffix[x]
    loadLen = _loadStore_thumb16_length[x]
    snm = _loadStore_thumb16_signedNotMask[x]
    return instrCls(encoding, 2, 1, res.d, op, append, loadLen, signedNotMask=snm)

# Sect A9.4
@InstructionDecoder(2, 3, '0101xxxmmmnnnddd')
def loadStoreInstructionDecoder_ThumbEERegister(res, encoding, condition):
    '''Decode ThumbEE ``str``, ``strh``, ``strb``, ``ldrsb``, ``ldr``, ``ldrh``,
    ``ldrb`` and ``ldrsh`` instructions of the type ``ldr r0, [r1, r2,
    lsl #2]``.'''
    x = res.x
    instrCls = LDRInstruction if x >= 0b11 else STRInstruction
    append = _loadStore_thumb16_suffix[x]
    loadLen = _loadStore_thumb16_length[x]
    snm = _loadStore_thumb16_signedNotMask[x]
    shiftAmount = _loadStore_thumbEE_shift[loadLen]
    op = Indirect(Register(res.n), Register(res.m), shiftType=SRTYPE_LSL, shiftAmount=shiftAmount)
    return instrCls(encoding, 2, 3, res.d, op, append, loadLen, signedNotMask=snm)

# Sect A6.2.4
@InstructionDecoder(2, 1, 'xxxxyiiiiinnnddd')
def loadStoreInstructionDecoder_Thumb16Immediate(res, encoding, condition):
    '''Decode 16-bit Thumb ``str``, ``strh``, ``strb``, ``ldr``, ``ldrh`` and
    ``ldrb`` instructions of the type ``ldr r0, [r1, #0x4]``.'''
    x = res.x - 0b0110
    if x < 0 or x > 2:
        return None
    instrCls = LDRInstruction if res.y else STRInstruction
    loadLen = (4, 1, 2)[x]
    op = Indirect(Register(res.n), Constant(res.i*loadLen))
    append = ('', 'b', 'h')[x]
    return instrCls(encoding, 2, 1, res.d, op, append, loadLen)

# Sect A6.2.4
@InstructionDecoder(2, 1, '1001xdddiiiiiiii')
def loadStoreInstructionDecoder_Thumb16SPRelative(res, encoding, condition):
    '''Decode 16-bit Thumb ``str`` and ``ldr`` instructions of the type ``ldr
    r0, [sp, #0x4]``.'''
    instrCls = LDRInstruction if res.x else STRInstruction
    op = Indirect(Register(REG_SP), Constant(res.i*4))
    return instrCls(encoding, 2, 1, res.d, op)

# Sect A8.6.59
@InstructionDecoder(2, 1, '01001dddiiiiiiii')
def loadStoreInstructionDecoder_Thumb16PCRelative(res, encoding, condition):
    'Decode the 16-bit Thumb ``ldr`` instruction of the type ``ldr r0, [pc, #0x4]``'
    op = Indirect(Register(REG_PC), Constant(res.i*4))
    return LDRInstruction(encoding, 2, 1, res.d, op, align=~3)

def _loadStore_thumb32_getInstrInfo(isLDR, x, s):
    instrCls = LDRInstruction if isLDR else STRInstruction
    append = ('b', 'h', '')[x]
    loadLen = 1 << x
    if s:
        append = 's' + append
        snm = -1 << (8*loadLen)
    else:
        snm = 0
    return (instrCls, append, loadLen, snm)

# Sect A6.3.7, A6.3.8, A6.3.9, A6.3.10
@InstructionDecoder(4, 1, '1111100suxxynnnn ddddiiiiiiiiiiii')
def loadStoreInstructionDecoder_Thumb32Immediate12(res, encoding, condition):
    '''Decode 32-bit Thumb ``ldr``, ``ldrh``, ``ldrsh``, ``ldrb``, ``ldrsb``,
    ``str``, ``strh`` and ``strb`` instructions of the type ``ldr.w r0, [r1,
    #0x23]``'''
    x = res.x
    u = res.u
    s = res.s
    n = res.n
    d = res.d
    isLDR = res.y
    if x == 0b11:
        return None     # undefined
    if n == REG_PC and not isLDR:
        return None     # undefined
    if n != REG_PC and not u:
        return None     # these are ldr.w r0, [r1, r2, lsl #3] 
    if (x == 0b10 or not isLDR) and s:
        return None     # undefined
    if isLDR and x != 0b10 and d == REG_PC:
        return None     # unallocated memory hint or 'pld'/'pli' instructions
    
    (instrCls, append, loadLen, snm) = _loadStore_thumb32_getInstrInfo(isLDR, x, s)
    align = ~3 if n == REG_PC else ~0
    
    op = Indirect(Register(n), Constant(res.i), positive=u)
    return instrCls(encoding, 4, 1, res.d, op, append, loadLen, align, signedNotMask=snm).forceWide()

# Sect A6.3.7, A6.3.8, A6.3.9, A6.3.10
@InstructionDecoder(4, 1, '1111100s0xxynnnn dddd1puwiiiiiiii')
def loadStoreInstructionDecoder_Thumb32Immediate8(res, encoding, condition):
    '''Decode 32-bit Thumb ``ldr``, ``ldrt``, ``ldrh``, ``ldrht`` ``ldrsh``,
    ``ldrsht``, ``ldrb``, ``ldrbt``, ``ldrsb``, ``ldrsbt``, ``str``, ``strt``,
    ``strh``, ``strht``, ``strb`` and ``strbt`` instructions of the type ``ldr
    r0, [r1, #-0x23]``'''
    n = res.n
    s = res.s
    d = res.d
    p = res.p
    u = res.u
    w = res.w
    x = res.x
    imm8 = res.i
    isLDR = res.y
    if n == REG_PC or x == 0b11:
        return None     # for literals, see loadStoreInstructionDecoder_Thumb32Immediate12
    if (x == 0b10 or not isLDR) and s:
        return None     # undefined
    if not p and not w:
        return None     # undefined
    if isLDR and x != 0b10 and d == REG_PC and p and not u and not w:
        return None     # unallocated memory hints and 'pld', 'pli'

    (instrCls, append, loadLen, snm) = _loadStore_thumb32_getInstrInfo(isLDR, x, s)
    if p and u and not w:
        append += 't'

    op = Indirect(Register(n), Constant(imm8), positive=u, writeBack=w, index=p)
    return instrCls(encoding, 4, 1, d, op, append, loadLen, signedNotMask=snm)

# Sect A6.3.7, A6.3.8, A6.3.9, A6.3.10
@InstructionDecoder(4, 1, '1111100s0xxynnnn dddd000000iimmmm')
def loadStoreInstructionDecoder_Thumb32Register(res, encoding, condition):
    n = res.n
    x = res.x
    s = res.s
    d = res.d
    isLDR = res.y
    if n == REG_PC or x == 0b11:
        return None     # undefined or literal
    if s and (x == 0b10 or not isLDR):
        return None     # undefined
    if isLDR and x != 0b10 and d == REG_PC:
        return None     # unallocated memory hints and 'pld', 'pli'

    (instrCls, append, loadLen, snm) = _loadStore_thumb32_getInstrInfo(isLDR, x, s)
    op = Indirect(Register(n), Register(res.m), shiftType=SRTYPE_LSL, shiftAmount=res.i)
    return instrCls(encoding, 4, 1, d, op, append, loadLen, signedNotMask=snm)
    
#===============================================================================
# Load/store multiple instruction decoder
# 
#  ldmXX, stmXX
#
#===============================================================================

def _parseRegList(x):
    i = 0
    while x:
        if x & 1:
            yield i
        i += 1
        x >>= 1

@InstructionDecoder(4, 0, '100PUEwynnnnrrrrrrrrrrrrrrrr')
def loadStoreMultipleInstructionDecoder_ARM(res, encoding, condition):
    instrCls = LDMInstruction if res.y else STMInstruction
    rl = RegisterList(*_parseRegList(res.r))
    return instrCls(encoding, 4, 0, res.n, rl,
                    writeBack=res.w, inc=res.U, before=res.P, excMode=res.E)

@InstructionDecoder(2, 1, '1100ynnnrrrrrrrr')
def loadStoreMultipleInstructionDecoder_Thumb16(res, encoding, condition):
    isLDM = res.y
    instrCls = LDMInstruction if isLDM else STMInstruction
    rl = RegisterList(*_parseRegList(res.r))
    return instrCls(encoding, 2, 1, res.n, rl,
                    writeBack=True, inc=isLDM, before=not isLDM)

@InstructionDecoder(2, 1, '1011y10Mrrrrrrrr')
def loadStoreMultipleInstructionDecoder_Thumb16PushPop(res, encoding, condition):
    isLDM = res.y
    instrCls = LDMInstruction if isLDM else STMInstruction
    rnumlist = _parseRegList(res.r)
    if res.M:
        firstReg = REG_PC if isLDM else REG_LR
        rl = RegisterList(firstReg, *rnumlist)
    else:
        rl = RegisterList(*rnumlist)
    return instrCls(encoding, 2, 1, REG_SP, rl,
                    writeBack=True, inc=isLDM, before=not isLDM)

@InstructionDecoder(4, 1, '1110100PU0wynnnn rrrrrrrrrrrrrrrr')
def loadStoreMultipleInstructionDecoder_Thumb32(res, encoding, condition):
    isInc = res.U
    isBefore = res.P
    if isInc == isBefore:        # these are 'srs' and 'rfe' instructions.
        return None
    instrCls = LDMInstruction if res.y else STMInstruction
    rl = RegisterList(*_parseRegList(res.r))
    return instrCls(encoding, 4, 1, res.n, rl,
                    writeBack=res.w, inc=isInc, before=isBefore).forceWide()
