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
from cpu.arm.operand import Constant, Register
from cpu.arm.status import Status
from cpu.memory import SimulatedROM
from cpu.arm.thread import Thread
from cpu.pointers import StackPointer
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


main()
