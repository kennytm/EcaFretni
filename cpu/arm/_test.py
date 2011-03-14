#!/usr/bin/env python3.1    
#    
#    _test.py ... Test cases.
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

from unittest import main, TestCase
import cpu.arm.instructions.core
from cpu.arm.instruction import Condition
from cpu.arm.operand import Constant, Register, Indirect, RegisterList
from cpu.arm.status import Status
from cpu.memory import SimulatedROM
from cpu.arm.thread import Thread
from cpu.pointers import StackPointer, Return
from cpu.arm.functions import *

class StatusTestCase(TestCase):
    def test_status(self):
        s = 0b10110010000000001110100000110000 
        st = Status(s)
        self.assertTrue(st.N)
        self.assertFalse(st.Z)
        self.assertTrue(st.C)
        self.assertTrue(st.V)
        self.assertFalse(st.Q)
        self.assertEqual(st.IT, 0b11101001)
        self.assertFalse(st.J)
        self.assertEqual(st.GE, 0)
        self.assertFalse(st.E)
        self.assertFalse(st.A)
        self.assertFalse(st.F)
        self.assertTrue(st.T)
        self.assertEqual(st.M, 16)
        self.assertEqual(st.value, s)
        self.assertEqual(st.instructionSet, 1)
        st.instructionSet = 2
        self.assertTrue(st.J)
        self.assertFalse(st.T)
        self.assertTrue(st.N)


class FunctionTestCase(TestCase):
    def test_signed(self):
        self.assertEqual(signed(-1<<32, 0x12345678), 0x12345678)
        self.assertEqual(signed(-1<<32, 0x87654321), -0x789abcdf)
    
    def test_rawShift(self):
        self.assertEqual(LSL_C(0xffffffff, 0x1234, 4), (0x12340, 0))
        self.assertEqual(LSL_C(0xffffffff, 0x1234, 20), (0x23400000, 1))
        self.assertEqual(LSL_C(0xffffffff, 0x1234, 21), (0x46800000, 0))
        self.assertEqual(LSL(0xffffffff, 0x1234, 4), 0x12340)
        self.assertEqual(LSL(0xffffffff, 0x1234, 20), 0x23400000)
        self.assertEqual(LSL(0xffffffff, 0x1234, 21), 0x46800000)

        self.assertEqual(LSR_C(0xffffffff, 0x876f0000, 4), (0x876f000, 0))
        self.assertEqual(LSR_C(0xffffffff, 0x876f0000, 20), (0x876, 1))
        self.assertEqual(LSR_C(0xffffffff, 0x876f0000, 21), (0x43b, 0))
        self.assertEqual(LSR(0xffffffff, 0x876f0000, 4), 0x876f000)
        self.assertEqual(LSR(0xffffffff, 0x876f0000, 20), 0x876)
        self.assertEqual(LSR(0xffffffff, 0x876f0000, 21), 0x43b)

        self.assertEqual(ASR_C(0xffffffff, 0x876f0000, 4), (0xf876f000, 0))
        self.assertEqual(ASR_C(0xffffffff, 0x876f0000, 20), (0xfffff876, 1))
        self.assertEqual(ASR_C(0xffffffff, 0x876f0000, 21), (0xfffffc3b, 0))
        self.assertEqual(ASR(0xffffffff, 0x876f0000, 4), 0xf876f000)
        self.assertEqual(ASR(0xffffffff, 0x876f0000, 20), 0xfffff876)
        self.assertEqual(ASR(0xffffffff, 0x876f0000, 21), 0xfffffc3b)
        self.assertEqual(ASR_C(0xffffffff, 0x789abcde, 4), (0x0789abcd, 1))

        self.assertEqual(ROR_C(0xff, 0b11001101, 1), (0b11100110, 1))
        self.assertEqual(ROR_C(0xff, 0b11001101, 2), (0b01110011, 0))
        self.assertEqual(ROR_C(0xff, 0b11001101, 7), (0b10011011, 1))
        self.assertEqual(ROR(0xff, 0b11001101, 1), 0b11100110)
        self.assertEqual(ROR(0xff, 0b11001101, 2), 0b01110011)
        self.assertEqual(ROR(0xff, 0b11001101, 7), 0b10011011)

        self.assertEqual(RRX_C(0xffffffff, 0x109df893, 1), (0x884efc49, 1))
        self.assertEqual(RRX_C(0xffffffff, 0x109df893, 0), (0x084efc49, 1))
        self.assertEqual(RRX_C(0xffffffff, 0x109df892, 0), (0x084efc49, 0))
        self.assertEqual(RRX(0xffffffff, 0x109df893, 1), 0x884efc49)
        self.assertEqual(RRX(0xffffffff, 0x109df893, 0), 0x084efc49)

    def test_decodeImm(self):
        self.assertEqual(DecodeImmShift(0, 0), (SRTYPE_LSL, 0))
        self.assertEqual(DecodeImmShift(0, 9), (SRTYPE_LSL, 9))
        self.assertEqual(DecodeImmShift(1, 0), (SRTYPE_LSR, 32))
        self.assertEqual(DecodeImmShift(1, 9), (SRTYPE_LSR, 9))
        self.assertEqual(DecodeImmShift(2, 0), (SRTYPE_ASR, 32))
        self.assertEqual(DecodeImmShift(2, 9), (SRTYPE_ASR, 9))
        self.assertEqual(DecodeImmShift(3, 0), (SRTYPE_RRX, 1))
        self.assertEqual(DecodeImmShift(3, 9), (SRTYPE_ROR, 9))

    def test_shift(self):
        self.assertEqual(Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 0, 1), (0x1234, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 0, 0), (0x1234, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 4, 1), (0x12340, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 4, 0), (0x12340, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 20, 1), (0x23400000, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x1234, SRTYPE_LSL, 20, 0), (0x23400000, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 0, 1), (0x876f0000, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 0, 0), (0x876f0000, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 4, 1), (0x876f000, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 4, 0), (0x876f000, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 20, 1), (0x876, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_LSR, 20, 0), (0x876, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 0, 1), (0x876f0000, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 0, 0), (0x876f0000, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 4, 1), (0xf876f000, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 4, 0), (0xf876f000, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 20, 1), (0xfffff876, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x876f0000, SRTYPE_ASR, 20, 0), (0xfffff876, 1))
        self.assertEqual(Shift_C(0xff, 0b11001101, SRTYPE_ROR, 0, 1), (0b11001101, 1))
        self.assertEqual(Shift_C(0xff, 0b11001101, SRTYPE_ROR, 0, 0), (0b11001101, 0))
        self.assertEqual(Shift_C(0xff, 0b11001101, SRTYPE_ROR, 1, 1), (0b11100110, 1))
        self.assertEqual(Shift_C(0xff, 0b11001101, SRTYPE_ROR, 1, 0), (0b11100110, 1))
        self.assertEqual(Shift_C(0xff, 0b11001101, SRTYPE_ROR, 2, 1), (0b01110011, 0))
        self.assertEqual(Shift_C(0xff, 0b11001101, SRTYPE_ROR, 2, 0), (0b01110011, 0))
        self.assertEqual(Shift_C(0xffffffff, 0x109df893, SRTYPE_RRX, 1, 1), (0x884efc49, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x109df893, SRTYPE_RRX, 1, 0), (0x084efc49, 1))
        self.assertEqual(Shift_C(0xffffffff, 0x109df892, SRTYPE_RRX, 1, 0), (0x084efc49, 0))
        
        self.assertEqual(Shift(0xffffffff, 0x1234, SRTYPE_LSL, 0, 1), 0x1234)
        self.assertEqual(Shift(0xffffffff, 0x1234, SRTYPE_LSL, 0, 0), 0x1234)
        self.assertEqual(Shift(0xffffffff, 0x1234, SRTYPE_LSL, 4, 1), 0x12340)
        self.assertEqual(Shift(0xffffffff, 0x1234, SRTYPE_LSL, 4, 0), 0x12340)
        self.assertEqual(Shift(0xffffffff, 0x1234, SRTYPE_LSL, 20, 1), 0x23400000)
        self.assertEqual(Shift(0xffffffff, 0x1234, SRTYPE_LSL, 20, 0), 0x23400000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 0, 1), 0x876f0000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 0, 0), 0x876f0000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 4, 1), 0x876f000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 4, 0), 0x876f000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 20, 1), 0x876)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_LSR, 20, 0), 0x876)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 0, 1), 0x876f0000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 0, 0), 0x876f0000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 4, 1), 0xf876f000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 4, 0), 0xf876f000)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 20, 1), 0xfffff876)
        self.assertEqual(Shift(0xffffffff, 0x876f0000, SRTYPE_ASR, 20, 0), 0xfffff876)
        self.assertEqual(Shift(0xff, 0b11001101, SRTYPE_ROR, 0, 1), 0b11001101)
        self.assertEqual(Shift(0xff, 0b11001101, SRTYPE_ROR, 0, 0), 0b11001101)
        self.assertEqual(Shift(0xff, 0b11001101, SRTYPE_ROR, 1, 1), 0b11100110)
        self.assertEqual(Shift(0xff, 0b11001101, SRTYPE_ROR, 1, 0), 0b11100110)
        self.assertEqual(Shift(0xff, 0b11001101, SRTYPE_ROR, 2, 1), 0b01110011)
        self.assertEqual(Shift(0xff, 0b11001101, SRTYPE_ROR, 2, 0), 0b01110011)
        self.assertEqual(Shift(0xffffffff, 0x109df893, SRTYPE_RRX, 1, 1), 0x884efc49)
        self.assertEqual(Shift(0xffffffff, 0x109df893, SRTYPE_RRX, 1, 0), 0x084efc49)
        self.assertEqual(Shift(0xffffffff, 0x109df892, SRTYPE_RRX, 1, 0), 0x084efc49)

    def test_expandImm(self):
        self.assertEqual(ThumbExpandImm(0x0ab), 0x000000ab)
        self.assertEqual(ThumbExpandImm(0x1ab), 0x00ab00ab)
        self.assertEqual(ThumbExpandImm(0x2ab), 0xab00ab00)
        self.assertEqual(ThumbExpandImm(0x3ab), 0xabababab)
        for i in range(8, 32):
            self.assertEqual(ThumbExpandImm(i << 7 | 0b1011010), 0b11011010 << (32-i))
        self.assertEqual(ThumbExpandImm_C(0x0ab, 0), (0x000000ab, 0))
        self.assertEqual(ThumbExpandImm_C(0x1ab, 0), (0x00ab00ab, 0))
        self.assertEqual(ThumbExpandImm_C(0x2ab, 0), (0xab00ab00, 0))
        self.assertEqual(ThumbExpandImm_C(0x3ab, 0), (0xabababab, 0))
        self.assertEqual(ThumbExpandImm_C(0x0ab, 1), (0x000000ab, 1))
        self.assertEqual(ThumbExpandImm_C(0x1ab, 1), (0x00ab00ab, 1))
        self.assertEqual(ThumbExpandImm_C(0x2ab, 1), (0xab00ab00, 1))
        self.assertEqual(ThumbExpandImm_C(0x3ab, 1), (0xabababab, 1))
        self.assertEqual(ThumbExpandImm_C(8 << 7 | 0b1011010, 0), (0b11011010 << 24, 1))
        self.assertEqual(ThumbExpandImm_C(8 << 7 | 0b1011010, 1), (0b11011010 << 24, 1))
        for i in range(9, 32):
            self.assertEqual(ThumbExpandImm_C(i << 7 | 0b1011010, 0), (0b11011010 << (32-i), 0))
            self.assertEqual(ThumbExpandImm_C(i << 7 | 0b1011010, 1), (0b11011010 << (32-i), 0))
        
        self.assertEqual(ARMExpandImm_C(0x0ab, 1), (0x000000ab, 1))
        self.assertEqual(ARMExpandImm_C(0x0ab, 0), (0x000000ab, 0))
        self.assertEqual(ARMExpandImm_C(0x1ab, 1), (0xc000002a, 1))
        self.assertEqual(ARMExpandImm_C(0x1ab, 0), (0xc000002a, 1))
        self.assertEqual(ARMExpandImm_C(0x2ab, 1), (0xb000000a, 1))
        self.assertEqual(ARMExpandImm_C(0x2ab, 0), (0xb000000a, 1))
        self.assertEqual(ARMExpandImm_C(0x3ab, 1), (0xac000002, 1))
        self.assertEqual(ARMExpandImm_C(0x3ab, 0), (0xac000002, 1))
        self.assertEqual(ARMExpandImm_C(0x4ab, 1), (0xab000000, 1))
        self.assertEqual(ARMExpandImm_C(0x4ab, 0), (0xab000000, 1))
        for i in range(5, 16):
            self.assertEqual(ARMExpandImm_C(i << 8 | 0xab, 0), (0xab << (32-2*i), 0))
            self.assertEqual(ARMExpandImm_C(i << 8 | 0xab, 1), (0xab << (32-2*i), 0))
        self.assertEqual(ARMExpandImm(0x0ab), 0x000000ab)
        self.assertEqual(ARMExpandImm(0x1ab), 0xc000002a)
        self.assertEqual(ARMExpandImm(0x2ab), 0xb000000a)
        self.assertEqual(ARMExpandImm(0x3ab), 0xac000002)
        self.assertEqual(ARMExpandImm(0x4ab), 0xab000000)
        for i in range(5, 16):
            self.assertEqual(ARMExpandImm(i << 8 | 0xab), 0xab << (32-2*i))

    def test_addWithCarry(self):
        self.assertEqual(AddWithCarry(0xff, 0x12, 0x34, 1), (0x47, 0, 0))
        self.assertEqual(AddWithCarry(0xff, 0x12, 0x34, 0), (0x46, 0, 0))
        self.assertEqual(AddWithCarry(0xff, 0x62, 0xef, 1), (0x52, 1, 0))
        self.assertEqual(AddWithCarry(0xff, 0x62, 0xef, 0), (0x51, 1, 0))
        self.assertEqual(AddWithCarry(0xff, 0x80, 0x7f, 1), (0x00, 1, 0))
        self.assertEqual(AddWithCarry(0xff, 0x80, 0x7f, 0), (0xff, 0, 0))
        self.assertEqual(AddWithCarry(0xff, 0x80, 0x80, 1), (0x01, 1, 1))
        self.assertEqual(AddWithCarry(0xff, 0x80, 0x80, 0), (0x00, 1, 1))
        self.assertEqual(AddWithCarry(0xff, 0x40, 0x40, 1), (0x81, 0, 1))
        self.assertEqual(AddWithCarry(0xff, 0x40, 0x40, 0), (0x80, 0, 1))

    def test_itAdvance(self):
        self.assertEqual(ITAdvance(0b00000000), 0)
        self.assertEqual(ITAdvance(0b10001000), 0)
        self.assertEqual(ITAdvance(0b10010100), 0b10001000)
        self.assertEqual(ITAdvance(0b10011010), 0b10010100)
        self.assertEqual(ITAdvance(0b10010101), 0b10001010)

    def test_pcAddr(self):
        self.assertEqual(fixPCAddrBX(0x1001), (0x1000, 1))
        self.assertEqual(fixPCAddrBX(0x1002), (0x1000, 0))
        self.assertEqual(fixPCAddrBX(0x1003), (0x1002, 1))
        self.assertEqual(fixPCAddrBX(0x1004), (0x1004, 0))
        
        self.assertEqual(fixPCAddrB(0x1001, 0), 0x1000)
        self.assertEqual(fixPCAddrB(0x1001, 1), 0x1000)
        self.assertEqual(fixPCAddrB(0x1002, 0), 0x1000)
        self.assertEqual(fixPCAddrB(0x1002, 1), 0x1002)
        self.assertEqual(fixPCAddrB(0x1003, 0), 0x1000)
        self.assertEqual(fixPCAddrB(0x1003, 1), 0x1002)
        self.assertEqual(fixPCAddrB(0x1004, 0), 0x1004)
        self.assertEqual(fixPCAddrB(0x1004, 1), 0x1004)

class OperandTestCase(TestCase):
    def test_indirect_operand(self):
        data = bytes.fromhex('67452301 efcdab89')
        srom = SimulatedROM(data, vmaddr=0x1000)
        thread = Thread(srom)
        thread.pc = 0x1000
        
        indir = Indirect(Register(REG_PC), Constant(8), positive=False)
        self.assertEqual(str(indir), '[pc, #-0x8]')
        self.assertEqual(indir.get(thread), 0x01234567)
        self.assertEqual(thread.pcRaw, 0x1000)
        
        thread.r[0] = 0x1000
        indir = Indirect(Register(0), Constant(4), writeBack=True)
        self.assertEqual(str(indir), '[r0, #0x4]!')
        self.assertEqual(indir.get(thread), 0x89abcdef)
        self.assertEqual(thread.r[0], 0x1004)

        thread.r[0] = 4
        indir = Indirect(Register(REG_SP), Register(0), index=False, writeBack=True)
        self.assertEqual(str(indir), '[sp], r0')
        indir.set(thread, 0xaabbccdd)
        self.assertEqual(thread.sp, StackPointer(4))
        self.assertEqual(thread.memory.get(StackPointer(0)), 0xaabbccdd)

        thread.r[0] = 3
        indir = Indirect(Register(REG_PC), Register(0), positive=False, shiftType=SRTYPE_LSL, shiftAmount=1)
        self.assertEqual(str(indir), '[pc, -r0, lsl #1]')
        self.assertEqual(indir.get(thread, length=2), 0x0123)
        
        thread.pc = 0x1002
        indir = Indirect(Register(REG_PC), Constant(8), positive=False)
        self.assertEqual(indir.get(thread, align=~3), 0x01234567)

    def test_register_list_str(self):
        rl = RegisterList(0, 1, 2, 3)
        self.assertEqual(str(rl), '{r0-r3}')
        
        rl = RegisterList(0, 2, 3)
        self.assertEqual(str(rl), '{r0, r2-r3}')

        rl = RegisterList(0, 2, 4)
        self.assertEqual(str(rl), '{r0, r2, r4}')

        rl = RegisterList(7)
        self.assertEqual(str(rl), '{r7}')

        rl = RegisterList()
        self.assertEqual(str(rl), '{}')

        rl = RegisterList(10, 11, 12, REG_SP, REG_LR, REG_PC)
        self.assertEqual(str(rl), '{r10-r11, ip, sp, lr, pc}')
        
    def test_register_list_getset(self):
        srom = SimulatedROM(bytes(), vmaddr=0x1000)
        thread = Thread(srom)
        thread.r[0] = 15
        thread.r[1] = 20
        thread.r[2] = 25
        thread.r[3] = 30
        thread.r[4] = 35
        
        rl = RegisterList(0, 1, REG_SP, 3, 4)
        self.assertEqual(list(rl.get(thread)), [15, 20, 30, 35, StackPointer(0)])
        self.assertEqual(rl.registers, (Register(0), Register(1), Register(3), Register(4), Register(REG_SP)))
        rl.set(thread, [2, 4, 6, 8, StackPointer(10)])
        self.assertEqual(thread.r[0], 2)
        self.assertEqual(thread.r[1], 4)
        self.assertEqual(thread.r[2], 25)
        self.assertEqual(thread.r[3], 6)
        self.assertEqual(thread.r[4], 8)
        self.assertEqual(thread.sp, StackPointer(10))

class DataProcTestCase(TestCase):
    def test_arm_adc(self):
        program = bytes.fromhex(
            '0200a1e0'  # adc    r0, r1, r2
            '7704b1e2'  # adcs   r0, r1, #0x77000000
            '8204a1e0'  # adc    r0, r1, r2, lsl #9
            '0200bd10'  # adcsne r0, sp, r2
            '6200a000'  # adceq  r0, r0, r2, rrx
            '7102a010'  # adcne  r0, r0, r1, ror r2
            '0120a2e2'  # adc    r2, r2, #0x1
            '01faa2e2'  # adc    pc, r2, #0x1000
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.r[1] = 0x12345678
        thread.r[2] = 17
        thread.pc = 0x1000
    
        # check simple addition
        instr = thread.execute()

        self.assertEqual(instr.encoding, 0x0a10002)
        self.assertEqual(instr.length, 4)
        self.assertEqual(instr.instructionSet, 0)
        self.assertEqual(instr.condition, Condition(Condition.AL))
        self.assertEqual(instr.width, "")
        self.assertEqual(instr.shiftType, 0)
        self.assertEqual(instr.shiftAmount, Constant(0))
        self.assertEqual(instr.mainOpcode(), 'adc')
        self.assertEqual(instr.opcode, 'adc')
        self.assertListEqual(instr.operands, [Register(0), Register(1), Register(2)])
        self.assertEqual(str(instr), "adc\tr0, r1, r2")

        self.assertEqual(thread.r[0], 0x12345689)
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x1004)
    
        # check flag setting
        instr = thread.execute()
        
        self.assertEqual(instr.encoding, 0x2b10477)
        self.assertEqual(instr.opcode, 'adcs')
        self.assertListEqual(instr.operands, [Register(0), Register(1), Constant(0x77000000)])
        self.assertEqual(str(instr), "adcs\tr0, r1, #0x77000000")
        
        self.assertEqual(thread.r[0], 0x89345678)
        self.assertTrue(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertTrue(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x1008)
    
        # check shifting & flag not set
        instr = thread.execute()

        self.assertEqual(instr.shiftType, 0)
        self.assertEqual(instr.shiftAmount, Constant(9))
        self.assertListEqual(instr.operands, [Register(0), Register(1), Register(2)])
        self.assertEqual(str(instr), "adc\tr0, r1, r2, lsl #9")

        self.assertEqual(thread.r[0], 0x12347878)
        self.assertTrue(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertTrue(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x100c)
        
        # check conditional & special pointers
        instr = thread.execute()
        self.assertEqual(instr.opcode, 'adcsne')
        self.assertListEqual(instr.operands, [Register(0), Register(13), Register(2)])
        self.assertEqual(str(instr), "adcsne\tr0, sp, r2")
        self.assertEqual(thread.r[0], StackPointer(17))
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x1010)
    
        # check skipping conditional
        instr = thread.execute()
        self.assertEqual(str(instr), "adceq\tr0, r0, r2, rrx")
        self.assertEqual(thread.r[0], StackPointer(17))
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x1014)
        
        # check ror & shift with register
        instr = thread.execute()
        self.assertEqual(str(instr), "adcne\tr0, r0, r1, ror r2")
        self.assertEqual(thread.r[0], StackPointer(17 + ((0x12345678*0x100000001)>>17&0xffffffff)))
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x1018)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "adc\tr2, r2, #0x1")
        self.assertEqual(thread.r[0], StackPointer(17 + ((0x12345678*0x100000001)>>17&0xffffffff)))
        self.assertEqual(thread.r[2], 18)
        self.assertEqual(thread.pcRaw, 0x101c)
        
        # check pc fixing
        instr = thread.execute()
        self.assertEqual(str(instr), "adc\tpc, r2, #0x1000")
        self.assertEqual(thread.r[0], StackPointer(17 + ((0x12345678*0x100000001)>>17&0xffffffff)))
        self.assertEqual(thread.r[2], 18)
        self.assertEqual(thread.instructionSet, 0)
        self.assertEqual(thread.pcRaw, 0x1010)

        # check loop
        instr = thread.execute()
        self.assertEqual(str(instr), "adceq\tr0, r0, r2, rrx")
        self.assertEqual(thread.r[0], StackPointer(17 + ((0x12345678*0x100000001)>>17&0xffffffff)))
        self.assertEqual(thread.pcRaw, 0x1014)
        
    def test_arm_adr(self):
        program = bytes.fromhex(
            '04008fe2'  # add r0, pc, #0x4
            '00108fe2'  # add r1, pc, #0x0
            '04204fe2'  # sub r2, pc, #0x4
            '08304fe2'  # sub r3, pc, #0x8
            '0c404fe2'  # sub r4, pc, #0xc
            '10504fe2'  # sub r5, pc, #0x10
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.pc = 0x1000

        instr = thread.execute()
        self.assertEqual(str(instr), "add\tr0, pc, #0x4")
        self.assertEqual(thread.r[0], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "add\tr1, pc, #0x0")
        self.assertEqual(thread.r[1], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "sub\tr2, pc, #0x4")
        self.assertEqual(thread.r[2], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "sub\tr3, pc, #0x8")
        self.assertEqual(thread.r[3], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "sub\tr4, pc, #0xc")
        self.assertEqual(thread.r[4], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "sub\tr5, pc, #0x10")
        self.assertEqual(thread.r[5], 0x100c)
        
    def test_arm_dataprocs(self):
        program = bytes.fromhex(
            '0c00a0e3'  # mov   r0, #0xc
            '071000e2'  # and   r1, r0, #0x7
            '812120e0'  # eor   r2, r0, r1, lsl #3
            '013052e0'  # subs  r3, r2, r1
            '02306140'  # rsbmi r3, r1, r2
            '724173e0'  # rsbs  r4, r3, r2, ror r1
            '015a84e2'  # add   r5, r4, #0x1000
            '0060d5e0'  # sbcs  r6, r5, r0
            '0260e6e2'  # rsc   r6, r6, #0x2
            '170090e3'  # orrs  r0, r0, #0x17
            '0100a0e1'  # mov   r1, r2
            '3661a0e1'  # lsr   r6, r6, r1
            '7760c6e3'  # bic   r6, r6, #0x77
            'a600e0e1'  # mvn   r0, r6, lsr #1
            'ff04b0e3'  # movs  r0, #0xff000000
            '0010f0e3'  # mvns  r1, #0
            '0120c0e0'  # sbc   r2, r0, r1
            '013060e0'  # rsb   r3, r0, r1
            '0340f2e0'  # rscs  r4, r2, r3
            '0f50e0e1'  # mvn   r5, pc
            '05f0e0e1'  # mvn   pc, r5
            '000090e0'  # adds  r0, r0, r0
            'bffda0e3'  # mov   pc, #0x2fc0

        )
        srom = SimulatedROM(program, vmaddr=0x2fc0)
        thread = Thread(srom)
        thread.pc = 0x2fc0
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'mov\tr0, #0xc')
        self.assertEqual(thread.r[0], 12)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'and\tr1, r0, #0x7')
        self.assertEqual(thread.r[1], 4)

        instr = thread.execute()
        self.assertEqual(str(instr), 'eor\tr2, r0, r1, lsl #3')
        self.assertEqual(thread.r[2], 44)

        instr = thread.execute()
        self.assertEqual(str(instr), 'subs\tr3, r2, r1')
        self.assertEqual(thread.r[3], 40)
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'rsbmi\tr3, r1, r2')
        self.assertEqual(thread.r[3], 40)
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)

        instr = thread.execute()
        self.assertEqual(str(instr), 'rsbs\tr4, r3, r2, ror r1')
        self.assertEqual(thread.r[4], 0xbfffffda)
        self.assertTrue(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)

        instr = thread.execute()
        self.assertEqual(str(instr), 'add\tr5, r4, #0x1000')
        self.assertEqual(thread.r[5], 0xc0000fda)

        instr = thread.execute()
        self.assertEqual(str(instr), 'sbcs\tr6, r5, r0')
        self.assertEqual(thread.r[6], 0xc0000fce)
        self.assertTrue(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)

        instr = thread.execute()
        self.assertEqual(str(instr), 'rsc\tr6, r6, #0x2')
        self.assertEqual(thread.r[6], 0x3ffff034)

        instr = thread.execute()
        self.assertEqual(str(instr), 'orrs\tr0, r0, #0x17')
        self.assertEqual(thread.r[0], 31)
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'mov\tr0, r1')
        self.assertEqual(thread.r[0], 4)

        instr = thread.execute()
        self.assertEqual(str(instr), 'lsr\tr6, r6, r1')
        self.assertEqual(thread.r[6], 0x3ffff03)

        instr = thread.execute()
        self.assertEqual(str(instr), 'bic\tr6, r6, #0x77')
        self.assertEqual(thread.r[6], 0x3ffff00)

        instr = thread.execute()
        self.assertEqual(str(instr), 'mvn\tr0, r6, lsr #1')
        self.assertEqual(thread.r[0], 0xfe00007f)

        instr = thread.execute()
        self.assertEqual(str(instr), 'movs\tr0, #0xff000000')
        self.assertEqual(thread.r[0], 0xff000000)
        self.assertTrue(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)

        instr = thread.execute()
        self.assertEqual(str(instr), 'mvns\tr1, #0x0')
        self.assertEqual(thread.r[1], 0xffffffff)
        self.assertTrue(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)

        instr = thread.execute()
        self.assertEqual(str(instr), 'sbc\tr2, r0, r1')
        self.assertEqual(thread.r[2], 0xff000001)

        instr = thread.execute()
        self.assertEqual(str(instr), 'rsb\tr3, r0, r1')
        self.assertEqual(thread.r[3], 0xffffff)

        instr = thread.execute()
        self.assertEqual(str(instr), 'rscs\tr4, r2, r3')
        self.assertEqual(thread.r[4], 0x1fffffe)
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)

        instr = thread.execute()
        self.assertEqual(str(instr), 'mvn\tr5, pc')
        self.assertEqual(thread.r[5], 0xffffcfeb)

        instr = thread.execute()
        self.assertEqual(str(instr), 'mvn\tpc, r5')
        self.assertEqual(thread.pcRaw, 0x3014)

        instr = thread.execute()
        self.assertEqual(str(instr), 'adds\tr0, r0, r0')
        self.assertEqual(thread.r[0], 0xfe000000)
        self.assertTrue(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)

        instr = thread.execute()
        self.assertEqual(str(instr), 'mov\tpc, #0x2fc0')
        self.assertEqual(thread.pcRaw, 0x2fc0)

        instr = thread.execute()
        self.assertEqual(str(instr), 'mov\tr0, #0xc')
        self.assertEqual(thread.r[0], 12)

    def test_thumb_adc(self):
        program = bytes.fromhex(
            '41f1 8420'  # adc.w  r0, r1, #0x84008400
            '4841'       # adcs   r0, r0, r1
            '41eb 4220'  # adc.w  r0, r1, r2, lsl #9
            '52eb 0f02'  # adcs.w r2, r2, pc
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.r[1] = 0x6543210f
        thread.r[2] = 12345
        thread.pc = 0x1000
        thread.instructionSet = 1
        
        instr = thread.execute()
        self.assertEqual(instr.encoding, 0xf1412084)
        self.assertEqual(instr.length, 4)
        self.assertEqual(instr.instructionSet, 1)
        self.assertEqual(instr.width, ".w")
        self.assertEqual(instr.shiftType, 0)
        self.assertEqual(instr.shiftAmount, Constant(0))
        self.assertEqual(instr.mainOpcode(), 'adc')
        self.assertEqual(instr.opcode, 'adc.w')
        self.assertListEqual(instr.operands, [Register(0), Register(1), Constant(0x84008400)])
        self.assertEqual(str(instr), "adc.w\tr0, r1, #0x84008400")
        
        self.assertEqual(thread.r[0], 0xe943a50f)
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x1004)
        
        
        instr = thread.execute()
        self.assertEqual(instr.encoding, 0x4148)
        self.assertEqual(instr.length, 2)
        self.assertEqual(instr.instructionSet, 1)
        self.assertEqual(instr.opcode, 'adcs')
        self.assertListEqual(instr.operands, [Register(0), Register(0), Register(1)])
        self.assertEqual(str(instr), "adcs\tr0, r0, r1")
        
        self.assertEqual(thread.r[0], 0x4e86c61e)
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x1006)
        
        instr = thread.execute()
        self.assertEqual(instr.encoding, 0xeb412042)
        self.assertEqual(instr.length, 4)
        self.assertEqual(instr.instructionSet, 1)
        self.assertEqual(instr.opcode, 'adc.w')
        self.assertListEqual(instr.operands, [Register(0), Register(1), Register(2)])
        self.assertEqual(instr.shiftType, 0)
        self.assertEqual(instr.shiftAmount, Constant(9))
        self.assertEqual(str(instr), "adc.w\tr0, r1, r2, lsl #9")
        
        self.assertEqual(thread.r[0], 0x65a39310)
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.V)
        self.assertFalse(thread.cpsr.Z)
        self.assertEqual(thread.pcRaw, 0x100a)
        
        instr = thread.execute()
        self.assertEqual(thread.r.pcOffset, 4)
        self.assertEqual(str(instr), "adcs.w\tr2, r2, pc")
        self.assertEqual(thread.r[2], 12345 + 0x100a + 4 + 1)
        self.assertEqual(thread.pcRaw, 0x100e)
        
    def test_thumb_adr(self):
        program = bytes.fromhex(
            '0ff2 0805' # addw	r5, pc, #8
            '01a6'      # add	r6, pc, #4
            '01a0'      # add	r0, pc, #4
            '00a1'      # add	r1, pc, #0
            '00a2'      # add	r2, pc, #0
            'aff2 0403' # subw	r3, pc, #4
            'aff2 0804' # subw	r4, pc, #8
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.pc = 0x1000
        thread.instructionSet = 1

        instr = thread.execute()
        self.assertEqual(str(instr), "addw\tr5, pc, #0x8")
        self.assertEqual(thread.r[5], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "add\tr6, pc, #0x4")
        self.assertEqual(thread.r[6], 0x100c)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "add\tr0, pc, #0x4")
        self.assertEqual(thread.r[0], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "add\tr1, pc, #0x0")
        self.assertEqual(thread.r[1], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "add\tr2, pc, #0x0")
        self.assertEqual(thread.r[2], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "subw\tr3, pc, #0x4")
        self.assertEqual(thread.r[3], 0x100c)

        instr = thread.execute()
        self.assertEqual(str(instr), "subw\tr4, pc, #0x8")
        self.assertEqual(thread.r[4], 0x100c)

    def test_thumb_dataprocs(self):
        program = bytes.fromhex(
            '4ff0 0300' # mov.w r0, #0x3
            '4fea 0001' # mov.w r1, r0
            '8140'      # lsls  r1, r1, r0
            '61f0 1302' # orn   r2, r1, #0x13
            'c2ea 0003' # pkhbt r3, r2, r0
            'b0eb 030f' # cmp.w r0, r3
            '10eb 030f' # cmn.w r0, r3
            '10ea 030f' # tst.w r0, r3
            '90ea 030f' # teq   r0, r3
            '1318'      # adds  r3, r2, r0
            '5a1c'      # adds  r2, r3, #0x1
            '7132'      # adds  r2, r2, #0x71
            '4242'      # rsbs  r2, r0, #0x0
            '8044'      # add   r8, r8, r0
            '81b0'      # sub   sp, sp, #0x4
            '02ad'      # add   r5, sp, #0x8
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.pc = 0x1000
        thread.r[8] = 1234
        self.assertEqual(thread.sp, StackPointer(0))
        thread.instructionSet = 1

        instr = thread.execute()
        self.assertEqual(str(instr), "mov.w\tr0, #0x3")
        self.assertEqual(thread.r[0], 3)

        instr = thread.execute()
        self.assertEqual(str(instr), "mov.w\tr1, r0")
        self.assertEqual(thread.r[1], 3)

        instr = thread.execute()
        self.assertEqual(str(instr), "lsls\tr1, r1, r0")
        self.assertEqual(thread.r[1], 24)

        instr = thread.execute()
        self.assertEqual(str(instr), "orn.w\tr2, r1, #0x13")
        self.assertEqual(thread.r[2], 0xfffffffc)

        instr = thread.execute()
        self.assertEqual(str(instr), "pkhbt.w\tr3, r2, r0")
        self.assertEqual(thread.r[3], 0x0000fffc)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "cmp.w\tr0, r3")
        self.assertTrue(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "cmn.w\tr0, r3")
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "tst.w\tr0, r3")
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertTrue(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "teq.w\tr0, r3")
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "adds\tr3, r2, r0")
        self.assertEqual(thread.r[3], 0xffffffff)
        self.assertTrue(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "adds\tr2, r3, #0x1")
        self.assertEqual(thread.r[2], 0)
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertTrue(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "adds\tr2, r2, #0x71")
        self.assertEqual(thread.r[2], 0x71)
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "rsbs\tr2, r0, #0x0")
        self.assertEqual(thread.r[2], 0xfffffffd)
        self.assertTrue(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "add\tr8, r8, r0")
        self.assertEqual(thread.r[8], 1237)

        instr = thread.execute()
        self.assertEqual(str(instr), "sub\tsp, sp, #0x4")
        self.assertEqual(thread.sp, StackPointer(-4))

        instr = thread.execute()
        self.assertEqual(str(instr), "add\tr5, sp, #0x8")
        self.assertEqual(thread.r[5], StackPointer(4))
    
    def test_thumb_test2(self):
        program = bytes.fromhex(
            '0920'      # movs  r0, #0x9
            '0101'      # lsls  r1, r0, #4
            '8842'      # cmp   r0, r1
            '0100'      # movs  r1, r0
            '8046'      # mov   r8, r0
            '4045'      # cmp   r0, r8
            '4af6 cd31' # movw  r1, #0xabcd
            'cff6 dc61' # movt  r1, #0xfedc
            '4fea 6112' # asr.w r2, r1, #5
            '62fa 00f3' # ror.w r3, r2, r0
            '00bf'      # nop
            'aff3 0080' # nop.w
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.pc = 0x1000
        thread.instructionSet = 1
        
        instr = thread.execute()
        self.assertEqual(str(instr), "movs\tr0, #0x9")
        self.assertEqual(thread.r[0], 9)
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "lsls\tr1, r0, #4")
        self.assertEqual(thread.r[1], 144)
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "cmp\tr0, r1")
        self.assertEqual(thread.r[0], 9)
        self.assertTrue(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "movs\tr1, r0")
        self.assertEqual(thread.r[1], 9)
        self.assertFalse(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "mov\tr8, r0")
        self.assertEqual(thread.r[8], 9)

        instr = thread.execute()
        self.assertEqual(str(instr), "cmp\tr0, r8")
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertTrue(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()
        self.assertEqual(str(instr), "movw\tr1, #0xabcd")
        self.assertEqual(thread.r[1], 0xabcd)

        instr = thread.execute()
        self.assertEqual(str(instr), "movt\tr1, #0xfedc")
        self.assertEqual(thread.r[1], 0xfedcabcd)

        instr = thread.execute()
        self.assertEqual(str(instr), "asr.w\tr2, r1, #5")
        self.assertEqual(thread.r[2], 0xFFF6E55E)

        instr = thread.execute()
        self.assertEqual(str(instr), "ror.w\tr3, r2, r0")
        self.assertEqual(thread.r[3], 0xAF7FFB72)

        instr = thread.execute()
        self.assertEqual(str(instr), "nop\t")

        instr = thread.execute()
        self.assertEqual(str(instr), "nop.w\t")

class IfThenTestCase(TestCase):
    def test_thumb_ifthen(self):
        program = bytes.fromhex(
            '8842'      # cmp   r0, r1
            '2cbf'      # ite   cs
            '421a'      # subcs r2, r0, r1
            'c0eb 0102' # rsbcc r2, r0, r1
            '002a'      # cmp   r2, #0x0
            '0dbf'      # iteet eq
            '0123'      # moveq r3, #0x1
            '0023'      # movne r3, #0x0
            '4ff0 ff32' # movne.w r2, #0xffffffff
            '9b18'      # addeq r3, r3, r2
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.instructionSet = 1
        thread.r[0] = 4
        thread.r[1] = 6
        thread.r[2] = 0
        thread.r[3] = 2
        
        thread.pc = 0x1000
        
        instr = thread.execute()
        self.assertEqual(str(instr), "cmp\tr0, r1")
        self.assertTrue(thread.cpsr.N)
        self.assertFalse(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "ite\tcs")

        instr = thread.execute()
        self.assertEqual(str(instr), "subcs\tr2, r0, r1")
        self.assertEqual(thread.r[2], 0)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "rsbcc.w\tr2, r0, r1")
        self.assertEqual(thread.r[2], 2)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "cmp\tr2, #0x0")
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "iteet\teq")
        
        instr = thread.execute()
        self.assertEqual(str(instr), "moveq\tr3, #0x1")
        self.assertEqual(thread.r[3], 2)
        
        instr = thread.execute()
        self.assertEqual(str(instr), "movne\tr3, #0x0")
        self.assertEqual(thread.r[3], 0)

        instr = thread.execute()
        self.assertEqual(str(instr), "movne.w\tr2, #0xffffffff")
        self.assertEqual(thread.r[2], 0xffffffff)

        instr = thread.execute()
        self.assertEqual(str(instr), "addeq\tr3, r3, r2")
        self.assertEqual(thread.r[3], 0)
        
        # try again with a different condition.
        thread.r[0] = 5
        thread.r[1] = 5
        thread.r[2] = 5
        thread.r[3] = 2
        thread.pc = 0x1000
        
        instr = thread.execute()    # cmp r0, r1
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertTrue(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)
        
        instr = thread.execute()    # ite cs
        
        instr = thread.execute()    # subcs r2, r0, r1
        self.assertEqual(thread.r[2], 0)

        instr = thread.execute()    # rsbcc r2, r0, r1
        self.assertEqual(thread.r[2], 0)
        
        instr = thread.execute()    # cmp r2, #0x0
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertTrue(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)

        instr = thread.execute()    # iteet eq
        
        instr = thread.execute()    # moveq r3, #1
        self.assertEqual(thread.r[3], 1)

        instr = thread.execute()    # movne r3, #0
        self.assertEqual(thread.r[3], 1)

        instr = thread.execute()    # movne.w r2, #-1
        self.assertEqual(thread.r[2], 0)

        instr = thread.execute()    # addeq r3, r2
        self.assertEqual(thread.r[3], 1)

class BranchTestCase(TestCase):
    def test_loop_program(self):
        program = bytes.fromhex(
            '1000a0e3'  # mov r0, #0x10
            '0010a0e3'  # mov r1, #0x0
            '0e20a0e1'  # mov r2, lr
            '020000fa'  # blx pc+0x8
            '000050e3'  # cmp r0, #0x0
            'fcffff1a'  # bne pc-0x10
            '12ff2fe1'  # bx  r2
            
            '0918'  # adds r1, r1, r0
            '0138'  # subs r0, r0, #0x1
            '7047'  # bx   lr
        )
        
        srom = SimulatedROM(program, vmaddr=0x2fdc)
        thread = Thread(srom)
        thread.pc = 0x2fdc
        
        instr = thread.execute()    # mov r0, #0x10
        instr = thread.execute()    # mov r1, #0x0
        instr = thread.execute()    # mov r2, lr
        self.assertEqual(str(instr), 'mov\tr2, lr')
        self.assertEqual(thread.r[2], Return)
        
        instr = thread.execute()    # blx pc+0x8
        self.assertEqual(str(instr), 'blx\tpc+0x8')
        self.assertEqual(thread.pcRaw, 0x2ff8)
        self.assertEqual(thread.lr, 0x2fec)
        self.assertTrue(thread.cpsr.T)
        
        instr = thread.execute()    # adds r1, r1, r0
        self.assertEqual(str(instr), 'adds\tr1, r1, r0')
        self.assertEqual(thread.r[1], 16)
        
        instr = thread.execute()    # subs r0, r0, #1
        instr = thread.execute()    # bx lr
        self.assertEqual(str(instr), 'bx\tlr')        
        self.assertEqual(thread.lr, 0x2fec)
        self.assertFalse(thread.cpsr.T)
        
        instr = thread.execute()    # cmp r0, #0
        self.assertEqual(str(instr), 'cmp\tr0, #0x0')
        self.assertFalse(thread.cpsr.N)
        self.assertTrue(thread.cpsr.C)
        self.assertFalse(thread.cpsr.Z)
        self.assertFalse(thread.cpsr.V)
        
        instr = thread.execute()    # bne pc-0x10
        self.assertEqual(str(instr), 'bne\tpc-0x10')
        self.assertEqual(thread.pcRaw, 0x2fe8)
        self.assertFalse(thread.cpsr.T)

        instr = thread.execute()    # blx pc+0x8
        self.assertEqual(str(instr), 'blx\tpc+0x8')
        self.assertEqual(thread.pcRaw, 0x2ff8)
        self.assertEqual(thread.lr, 0x2fec)
        self.assertTrue(thread.cpsr.T)
        
        thread.run()
        
        self.assertEqual(thread.pcRaw, Return)
        self.assertEqual(thread.r[0], 0)
        self.assertEqual(thread.r[1], 136)
        self.assertEqual(thread.r[2], Return)        
        
    def test_crazy_jump(self):
        program = bytes.fromhex(
            '4ff0 0000' # mov.w r0, #0x0
            '0028'      # cmp   r0, #0x0
            '0ad0'      # beq   0x2ff6
            '00f0 0a80' # beq.w 0x2ff8
            '0ff2 1401' # addw  r1, pc, #0x14
            '8847'      # blx   r1
            '00f0 00f8' # bl    0x2fee
            '00f0 06e8' # blx   0x2ffc
            'cef3 008f' # bxj   lr
            'f3e7'      # b     0x2fe0
            'fff7 f4bf' # b.w   0x2fe4
            
            '1eff2fe1'  # bx    lr
        )
        srom = SimulatedROM(program, vmaddr=0x2fd8)
        thread = Thread(srom)
        thread.pc = 0x2fd8
        thread.instructionSet = 1
        
        self.assertEqual(thread.pcRaw, 0x2fd8)
        thread.execute()    # mov.w r0, #0x0
        
        self.assertEqual(thread.pcRaw, 0x2fdc)
        thread.execute()    # cmp r0, #0x0
        
        self.assertEqual(thread.pcRaw, 0x2fde)
        thread.execute()    # beq 0x2ff6
        
        self.assertEqual(thread.pcRaw, 0x2ff6)
        thread.execute()    # b 0x2fe0

        self.assertEqual(thread.pcRaw, 0x2fe0)
        thread.execute()    # beq.w 0x2ff8

        self.assertEqual(thread.pcRaw, 0x2ff8)
        thread.execute()    # b.w 0x2fe4

        self.assertEqual(thread.pcRaw, 0x2fe4)
        thread.execute()    # addw r1, pc, #0x20
        self.assertEqual(thread.r[1], 0x2ffc)
        
        self.assertEqual(thread.pcRaw, 0x2fe8)
        thread.execute()    # blx r1
        
        self.assertEqual(thread.pcRaw, 0x2ffc)
        thread.execute()    # bx lr
        
        self.assertEqual(thread.pcRaw, 0x2fea)
        thread.execute()    # bl 0x2fee
        
        self.assertEqual(thread.pcRaw, 0x2fee)
        thread.execute()    # blx 0x2ffc

        self.assertEqual(thread.pcRaw, 0x2ffc)
        thread.execute()    # bx lr

        self.assertEqual(thread.pcRaw, 0x2ff2)
        instr = thread.fetch()    # bxj lr
        self.assertEqual(str(instr), 'bxj\tlr')
    
    def test_onbranch(self):
        program = bytes.fromhex(
            '00b5'      # push  {lr}
            '0420'      # movs  r0, #0x4
            '0721'      # movs  r1, #0x7
            '8842'      # cmp   r0, r1
            '00d1'      # bne   0x2fec
            '00bd'      # pop   {pc}
            '401a'      # subs  r0, r0, r1
            '00f0 02e8' # blx   0x2ff4
            'fae7'      # b     0x2fea
        )
        srom = SimulatedROM(program, vmaddr=0x2fe0)
        thread = Thread(srom)
        thread.pc = 0x2fe0
        thread.instructionSet = 1
        
        branchLst = []
        
        def thread_on_branch(prevLoc, instr, thread_):
            branchLst.append((prevLoc, thread_.pcRaw))
            if instr.mainOpcode() in {'bl', 'blx'}:
                thread_.forceReturn()
            
        thread.onBranch = thread_on_branch
        thread.run()
        
        self.assertListEqual(branchLst, [
            (0x2fe8, 0x2fec),
            (0x2fee, 0x2ff4),
            (0x2ff2, 0x2fea),
            (0x2fea, Return)
        ])
        
        

class LoadStoreTestCase(TestCase):
    def test_arm_word(self):
        program = bytes.fromhex(
            '1200a0e3'  # mov   r0, #0x12
            '00008de5'  # str   r0, [sp]
            '1c109fe5'  # ldr   r1, [pc, #0x1c]
            '04100de5'  # str   r1, [sp, #-0x4]
            '04204de2'  # sub   r2, sp, #0x4
            '0430b2e5'  # ldr   r3, [r2, #0x4]!
            '044012e4'  # ldr   r4, [r2], #-0x4
            '24c04fe2'  # sub   ip, pc, #0x24
            '0150a0e3'  # mov   r5, #0x1
            '05c102e7'  # str   ip, [r2, -r5, lsl #2]
            '05f112e7'  # ldr   pc, [r2, -r5, lsl #2]
            '78563412'  # .word 0x12345678
        )
        srom = SimulatedROM(program, vmaddr=0x2fd0)
        thread = Thread(srom)
        thread.pc = 0x2fd0
        
        instr = thread.execute()    # mov r0, #0x12
        instr = thread.execute()    # str r0, [sp]
        self.assertEqual(str(instr), 'str\tr0, [sp]')
        self.assertEqual(thread.sp, StackPointer(0))
        self.assertEqual(thread.memory.stack.get(0), 0x12)
        
        instr = thread.execute()    # ldr r1, [pc, #0]
        self.assertEqual(str(instr), 'ldr\tr1, [pc, #0x1c]')
        self.assertEqual(thread.r[1], 0x12345678)
        
        instr = thread.execute()    # str r1, [sp, #-0x4]
        self.assertEqual(str(instr), 'str\tr1, [sp, #-0x4]')
        self.assertEqual(thread.sp, StackPointer(0))
        self.assertEqual(thread.memory.stack.get(0), 0x12)
        self.assertEqual(thread.memory.stack.get(-4), 0x12345678)
        
        instr = thread.execute()    # sub r2, sp, #0x4
        self.assertEqual(thread.r[2], StackPointer(-4))
        
        instr = thread.execute()    # ldr r3, [r2, #0x4]!
        self.assertEqual(str(instr), 'ldr\tr3, [r2, #0x4]!')
        self.assertEqual(thread.r[2], StackPointer(0))
        self.assertEqual(thread.r[3], 0x12)
        
        instr = thread.execute()    # ldr r4, [r2], #-0x4
        self.assertEqual(str(instr), 'ldr\tr4, [r2], #-0x4')
        self.assertEqual(thread.r[2], StackPointer(-4))
        self.assertEqual(thread.r[4], 0x12)

        instr = thread.execute()    # sub ip, pc, #0x24
        instr = thread.execute()    # mov r5, #0x1
        self.assertEqual(thread.ip, 0x2fd0)

        instr = thread.execute()    # str ip, [r2, -r5, lsl #2]
        self.assertEqual(str(instr), 'str\tip, [r2, -r5, lsl #2]')
        self.assertEqual(thread.r[2], StackPointer(-4))
        self.assertEqual(thread.memory.stack.get(0), 0x12)
        self.assertEqual(thread.memory.stack.get(-4), 0x12345678)
        self.assertEqual(thread.memory.stack.get(-8), 0x2fd0)

        instr = thread.execute()    # ldr pc, [r2, -r5, lsl #2]
        self.assertEqual(str(instr), 'ldr\tpc, [r2, -r5, lsl #2]')
        self.assertEqual(thread.pcRaw, 0x2fd0)

    def test_thumb_word(self):
        program = bytes.fromhex(
            '1220'      # movs  r0, #0x12
            '0090'      # str   r0, [sp]
            '0649'      # ldr   r1, [pc, #0x18]
            '0191'      # str   r1, [sp, #0x4]
            '01aa'      # add   r2, sp, #0x4
            '52f8 043d' # ldr   r3, [r2, #-0x4]!
            '52f8 044b' # ldr   r4, [r2], #0x4
            'aff2 140c' # subw  ip, pc, #0x14
            '0125'      # movs  r5, #0x1
            '42f8 35c0' # str   ip, [r2, r5, lsl #3]
            '52f8 35f0' # ldr   pc, [r2, r5, lsl #3]
            '78563412'  # .word 0x12345678
        )
        srom = SimulatedROM(program, vmaddr=0x2fd0)
        thread = Thread(srom)
        thread.pc = 0x2fd0
        thread.instructionSet = 1

        instr = thread.execute()    # mov r0, #0x12
        instr = thread.execute()    # str r0, [sp]
        self.assertEqual(str(instr), 'str\tr0, [sp]')
        self.assertEqual(thread.sp, StackPointer(0))
        self.assertEqual(thread.memory.stack.get(0), 0x12)
        
        instr = thread.execute()    # ldr r1, [pc, #0x18]
        self.assertEqual(str(instr), 'ldr\tr1, [pc, #0x18]')
        self.assertEqual(thread.r[1], 0x12345678)
        
        instr = thread.execute()    # str r1, [sp, #0x4]
        self.assertEqual(str(instr), 'str\tr1, [sp, #0x4]')
        self.assertEqual(thread.sp, StackPointer(0))
        self.assertEqual(thread.memory.stack.get(0), 0x12)
        self.assertEqual(thread.memory.stack.get(4), 0x12345678)
        
        instr = thread.execute()    # add r2, sp, #0x4
        self.assertEqual(thread.r[2], StackPointer(4))
        
        instr = thread.execute()    # ldr r3, [r2, #-0x4]!
        self.assertEqual(str(instr), 'ldr\tr3, [r2, #-0x4]!')
        self.assertEqual(thread.r[2], StackPointer(0))
        self.assertEqual(thread.r[3], 0x12)
        
        instr = thread.execute()    # ldr r4, [r2], #0x4
        self.assertEqual(str(instr), 'ldr\tr4, [r2], #0x4')
        self.assertEqual(thread.r[2], StackPointer(4))
        self.assertEqual(thread.r[4], 0x12)

        instr = thread.execute()    # subw ip, pc, #0x14
        instr = thread.execute()    # movs r5, #0x1
        self.assertEqual(thread.ip, 0x2fd0)

        instr = thread.execute()    # str ip, [r2, r5, lsl #3]
        self.assertEqual(str(instr), 'str\tip, [r2, r5, lsl #3]')
        self.assertEqual(thread.r[2], StackPointer(4))
        self.assertEqual(thread.memory.stack.get(0), 0x12)
        self.assertEqual(thread.memory.stack.get(4), 0x12345678)
        self.assertEqual(thread.memory.stack.get(12), 0x2fd0)

        instr = thread.execute()    # ldr pc, [r2, r5, lsl #3]
        self.assertEqual(str(instr), 'ldr\tpc, [r2, r5, lsl #3]')
        self.assertEqual(thread.pcRaw, 0x2fd0)

    def test_thumb_extra(self):
        program = bytes.fromhex(
            '0010e0e3'  # mvn   r1, #0x0
            '0010ade4'  # strt  r1, [sp]
            '1000dfe5'  # ldrb  r0, [pc, #0x10]
            '0300ede4'  # strbt r0, [sp], #0x3
            '0100cde4'  # strb  r0, [sp], #0x1
            '0120dde7'  # ldrb  r2, [sp, r1]
            '0030bde4'  # ldrt  r3, [sp]
            '000000fa'  # blx   pc+0
            
            '12345678'  # .byte 0x12, 0x34, 0x56, 0x78
            
            '0020'      # movs  r0, #0x0
            '5fea 0d02' # movs.w r2, sp
            '1358'      # ldr   r3, [r2, r0]
            '145a'      # ldrh  r4, [r2, r0]
            '155e'      # ldrsh r5, [r2, r0]
            '165c'      # ldrb  r6, [r2, r0]
            '1756'      # ldrsb r7, [r2, r0]
            '1154'      # strb  r1, [r2, r0]
            '1052'      # strh  r0, [r2, r0]
            '1150'      # str   r1, [r2, r0]
            'c2f8 0410' # str.w r1, [r2, #0x4]
            'd080'      # strh  r0, [r2, #0x6]
            'd171'      # strb  r1, [r2, #0x7]
            '5368'      # ldr   r3, [r2, #0x4]
            '9488'      # ldrh  r4, [r2, #0x4]
            '32f9 045e' # ldrsht r5, [r2, #0x4]
            '1679'      # ldrb  r6, [r2, #0x4]
            '12f9 047f' # ldrsb r7, [r2, #0x4]!
            '42f8 0469' # str   r6, [r2], #-0x4
            '7047'      # bx    lr
        )
        srom = SimulatedROM(program, vmaddr=0x2fac)
        thread = Thread(srom)
        thread.pc = 0x2fac
        
        instr = thread.execute()    # mvn r1, #0x0
        self.assertEqual(thread.r[1], 0xffffffff)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'strt\tr1, [sp]')
        self.assertEqual(thread.memory.get(StackPointer(0)), 0xffffffff)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrb\tr0, [pc, #0x10]')
        self.assertEqual(thread.r[0], 0x12)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'strbt\tr0, [sp], #0x3')
        self.assertEqual(thread.sp, StackPointer(3))
        self.assertEqual(thread.memory.get(StackPointer(0)), 0xffffff12)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'strb\tr0, [sp], #0x1')
        self.assertEqual(thread.sp, StackPointer(4))
        self.assertEqual(thread.memory.get(StackPointer(0)), 0x12ffff12)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrb\tr2, [sp, r1]')
        self.assertEqual(thread.r[2], 0x12)

        thread.memory.set(StackPointer(4), 0xabcdef01)
        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrt\tr3, [sp]')
        self.assertEqual(thread.r[3], 0xabcdef01)
        
        instr = thread.execute()    # blx pc+0
        self.assertEqual(thread.pcRaw, 0x2fd0)
        self.assertEqual(thread.instructionSet, 1)
        
        instr = thread.execute()    # movs r0, #0
        instr = thread.execute()    # movs r2, sp
        self.assertEqual(thread.r[0], 0)
        self.assertEqual(thread.r[2], StackPointer(4))
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'ldr\tr3, [r2, r0]')
        self.assertEqual(thread.r[3], 0xabcdef01)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrh\tr4, [r2, r0]')
        self.assertEqual(thread.r[4], 0xef01)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrsh\tr5, [r2, r0]')
        self.assertEqual(thread.r[5], 0xffffef01)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrb\tr6, [r2, r0]')
        self.assertEqual(thread.r[6], 0x01)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrsb\tr7, [r2, r0]')
        self.assertEqual(thread.r[7], 0x01)

        instr = thread.execute()
        self.assertEqual(str(instr), 'strb\tr1, [r2, r0]')
        self.assertEqual(thread.memory.get(StackPointer(4)), 0xabcdefff)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'strh\tr0, [r2, r0]')
        self.assertEqual(thread.memory.get(StackPointer(4)), 0xabcd0000)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'str\tr1, [r2, r0]')
        self.assertEqual(thread.memory.get(StackPointer(4)), 0xffffffff)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'str.w\tr1, [r2, #0x4]')
        self.assertEqual(thread.memory.get(StackPointer(8)), 0xffffffff)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'strh\tr0, [r2, #0x6]')
        self.assertEqual(thread.memory.get(StackPointer(8)), 0x0000ffff)

        instr = thread.execute()
        self.assertEqual(str(instr), 'strb\tr1, [r2, #0x7]')
        self.assertEqual(thread.memory.get(StackPointer(8)), 0xff00ffff)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldr\tr3, [r2, #0x4]')
        self.assertEqual(thread.r[3], 0xff00ffff)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrh\tr4, [r2, #0x4]')
        self.assertEqual(thread.r[4], 0xffff)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrsht\tr5, [r2, #0x4]')
        self.assertEqual(thread.r[5], 0xffffffff)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrb\tr6, [r2, #0x4]')
        self.assertEqual(thread.r[6], 0xff)

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldrsb\tr7, [r2, #0x4]!')
        self.assertEqual(thread.r[2], StackPointer(8))
        self.assertEqual(thread.r[7], 0xffffffff)

        instr = thread.execute()
        self.assertEqual(str(instr), 'str\tr6, [r2], #-0x4')
        self.assertEqual(thread.r[2], StackPointer(4))
        self.assertEqual(thread.memory.get(StackPointer(8)), 0xff)
    
    def test_arm_multiple(self):
        program = bytes.fromhex(
            '10808fe2'  # add   r8, pc, #0x10
            '0f00b8e9'  # ldmib r8!, {r0-r3}
            '0f002de9'  # push  {r0-r3}
            '001e9de8'  # ldmia sp, {r9-r11, ip}
            'f000bde8'  # pop   {r4-r7}
            '550018e8'  # ldmda r8, {r0, r2, r4, r6}
            '00000000 78563412 f0debc9a e0ac6824 df9b5713'
                        # .word 0, 0x12345678, 0x9abcdef0, 0x2468ace0, 0x13579bdf
        )
        srom = SimulatedROM(program, vmaddr=0x2fd4)
        thread = Thread(srom)
        thread.pc = 0x2fd4
        
        instr = thread.execute()    # add r8, pc, #0x10
        self.assertEqual(thread.r[8], 0x2fec)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'ldmib\tr8!, {r0-r3}')
        self.assertEqual(thread.r[0], 0x12345678)
        self.assertEqual(thread.r[1], 0x9abcdef0)
        self.assertEqual(thread.r[2], 0x2468ace0)
        self.assertEqual(thread.r[3], 0x13579bdf)
        self.assertEqual(thread.r[8], 0x2ffc)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'push\t{r0-r3}')
        self.assertEqual(thread.memory.get(StackPointer(-16)), 0x12345678)
        self.assertEqual(thread.memory.get(StackPointer(-12)), 0x9abcdef0)
        self.assertEqual(thread.memory.get(StackPointer(-8)), 0x2468ace0)
        self.assertEqual(thread.memory.get(StackPointer(-4)), 0x13579bdf)
        self.assertEqual(thread.sp, StackPointer(-16))

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldmia\tsp, {r9-r11, ip}')
        self.assertEqual(thread.r[9], 0x12345678)
        self.assertEqual(thread.r[10], 0x9abcdef0)
        self.assertEqual(thread.r[11], 0x2468ace0)
        self.assertEqual(thread.ip, 0x13579bdf)
        self.assertEqual(thread.sp, StackPointer(-16))

        instr = thread.execute()
        self.assertEqual(str(instr), 'pop\t{r4-r7}')
        self.assertEqual(thread.r[4], 0x12345678)
        self.assertEqual(thread.r[5], 0x9abcdef0)
        self.assertEqual(thread.r[6], 0x2468ace0)
        self.assertEqual(thread.r[7], 0x13579bdf)
        self.assertEqual(thread.sp, StackPointer(0))
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'ldmda\tr8, {r0, r2, r4, r6}')
        self.assertEqual(thread.r[0], 0x12345678)
        self.assertEqual(thread.r[2], 0x9abcdef0)
        self.assertEqual(thread.r[4], 0x2468ace0)
        self.assertEqual(thread.r[6], 0x13579bdf)
        self.assertEqual(thread.r[8], 0x2ffc)

    def test_thumb_multiple(self):
        program = bytes.fromhex(
            '04a7'      # add   r7, pc, #0x10
            '0fcf'      # ldmia r7!, {r0-r3}
            '0fb4'      # push  {r0-r3}
            '9de8 001e' # ldmia.w sp, {r9-r11, ip}
            'bde8 7001' # pop.w {r4-r6, r8}
            '17e9 5500' # ldmdb.w r7, {r0, r2, r4, r6}
            '00bf'      # nop
            '78563412 f0debc9a e0ac6824 df9b5713'
                        # .word 0x12345678, 0x9abcdef0, 0x2468ace0, 0x13579bdf
        )
        srom = SimulatedROM(program, vmaddr=0x2fdc)
        thread = Thread(srom)
        thread.instructionSet = 1
        thread.pc = 0x2fdc
        
        instr = thread.execute()    # add r7, pc, #0x10
        self.assertEqual(thread.r[7], 0x2ff0)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'ldmia\tr7!, {r0-r3}')
        self.assertEqual(thread.r[0], 0x12345678)
        self.assertEqual(thread.r[1], 0x9abcdef0)
        self.assertEqual(thread.r[2], 0x2468ace0)
        self.assertEqual(thread.r[3], 0x13579bdf)
        self.assertEqual(thread.r[7], 0x3000)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'push\t{r0-r3}')
        self.assertEqual(thread.memory.get(StackPointer(-16)), 0x12345678)
        self.assertEqual(thread.memory.get(StackPointer(-12)), 0x9abcdef0)
        self.assertEqual(thread.memory.get(StackPointer(-8)), 0x2468ace0)
        self.assertEqual(thread.memory.get(StackPointer(-4)), 0x13579bdf)
        self.assertEqual(thread.sp, StackPointer(-16))

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldmia.w\tsp, {r9-r11, ip}')
        self.assertEqual(thread.r[9], 0x12345678)
        self.assertEqual(thread.r[10], 0x9abcdef0)
        self.assertEqual(thread.r[11], 0x2468ace0)
        self.assertEqual(thread.ip, 0x13579bdf)
        self.assertEqual(thread.sp, StackPointer(-16))
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'pop.w\t{r4-r6, r8}')
        self.assertEqual(thread.r[4], 0x12345678)
        self.assertEqual(thread.r[5], 0x9abcdef0)
        self.assertEqual(thread.r[6], 0x2468ace0)
        self.assertEqual(thread.r[8], 0x13579bdf)
        self.assertEqual(thread.sp, StackPointer(0))

        instr = thread.execute()
        self.assertEqual(str(instr), 'ldmdb.w\tr7, {r0, r2, r4, r6}')
        self.assertEqual(thread.r[0], 0x12345678)
        self.assertEqual(thread.r[2], 0x9abcdef0)
        self.assertEqual(thread.r[4], 0x2468ace0)
        self.assertEqual(thread.r[6], 0x13579bdf)
        self.assertEqual(thread.r[7], 0x3000)

    def test_thumb_multiple_extra(self):
        program = bytes.fromhex(
            '0420'      # movs  r0, #0x4
            '6946'      # mov   r1, sp
            '21e9 0500' # stmdb.w r1!, {r0, r2}
            '01b5'      # push  {r0, lr}
            '0720'      # movs  r0, #0x7
            '01bd'      # pop   {r0, pc}
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.pc = 0x1000
        thread.instructionSet = 1
        
        thread.execute()    # movs r0, #0x4
        thread.execute()    # mov r1, sp
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'stmdb.w\tr1!, {r0, r2}')
        self.assertEqual(thread.r[1], StackPointer(-8))
        self.assertEqual(thread.memory.get(StackPointer(-8)), 4)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'push\t{r0, lr}')
        self.assertEqual(thread.sp, StackPointer(-8))
        self.assertEqual(thread.memory.get(StackPointer(-4)), Return)
        self.assertEqual(thread.memory.get(StackPointer(-8)), 4)
        
        thread.execute()    # movs r0, #0x7
        self.assertEqual(thread.r[0], 7)
        
        instr = thread.execute()
        self.assertEqual(str(instr), 'pop\t{r0, pc}')
        self.assertEqual(thread.sp, StackPointer(0))
        self.assertEqual(thread.r[0], 4)
        self.assertEqual(thread.pcRaw, Return)


class MiscInstrTestCase(TestCase):
    def test_arm_special_move(self):
        program = bytes.fromhex(
            '230100e3'  # movw  r0, #0x123
            '04f020e3'  # sev
            '320445e3'  # movt  r0, #0x5432
        )
        srom = SimulatedROM(program, vmaddr=0x1000)
        thread = Thread(srom)
        thread.pc = 0x1000

        instr = thread.execute()
        self.assertEqual(str(instr), "movw\tr0, #0x123")
        self.assertEqual(thread.r[0], 0x123)

        instr = thread.execute()
        self.assertEqual(str(instr), "sev\t")

        instr = thread.execute()
        self.assertEqual(str(instr), "movt\tr0, #0x5432")
        self.assertEqual(thread.r[0], 0x54320123)
    
        


main()
