#    
#    status.py ... ARM status register
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
import sys

def __fixIT(t):
    return (t >> 6) + ((t & 0b111111) << 2)

def __unfixIT(t):
    return (t >> 2) + ((t & 0b11) << 6)


class Status(BitPattern('NZCVQttJ ____gggg ttttttEA IFTMMMMM', rename={'g':'GE', 't':'IT'}, fixUps={'IT':(__fixIT, __unfixIT)}, className='Status').returnType):
    '''
    This class represents the content of a status register. It stores
    information about the current executing thread. 
    
    .. note::
    
        The emulator currently do not respect the :attr:`A`, :attr:`I`,
        :attr:`F` and :attr:`M` fields. The program always run in the least
        restrictive mode, all interrupts are ignored and aborts are handled by
        software.

    .. attribute:: N
    
        Check/set the negative ("N") flag
       
    .. attribute:: Z
    
        Check/set the zero ("Z") flag
    
    .. attribute:: C
    
        Check/set the carry ("C") flag
    
    .. attribute:: V
    
        Check/set the overflow ("V") flag
    
    .. attribute:: Q
    
        Check/set the saturation ("Q") flag
        
    .. attribute:: IT
    
        Get/set the executive state of the Thumb ``IT`` (if-then) instruction.
        
    .. attribute:: J
    
        Check/set the Jazelle ("J") bit.
        
    .. attribute:: GE
    
        Get/set the NEON greater than or equal ("GE") flags.
    
    .. attribute:: E
    
        Check/set the endian ("E") flag, with 1 being big-endian.
        
        .. note:: Setting this flag has no effect on the emulator. It will
                  always run in little-endian mode.
    
    .. attribute:: A
    
        Check/set the asynchronous abort disable ("A") bit.
    
    .. attribute:: I
    
        Check/set the interrupt disable ("I") bit.
        
    .. attribute:: F
    
        Check/set the fast interrupt disable ("F") bit.
    
    .. attribute:: T
    
        Check/set the Thumb mode ("T") flag.
    
    .. attribute:: M

        Get/set the mode ("M") field.
        
        +-------+-------------------------------+
        | Value | Processing mode               |
        +=======+===============================+
        | 16    | User                          |
        +-------+-------------------------------+
        | 17    | FIQ (Fast interrupt)          |
        +-------+-------------------------------+
        | 18    | IRQ (Interrupt)               |
        +-------+-------------------------------+
        | 19    | Supervisor (i.e. kernel mode) |
        +-------+-------------------------------+
        | 22    | Monitor                       |
        +-------+-------------------------------+
        | 23    | Abort                         |
        +-------+-------------------------------+
        | 27    | Undefined                     |
        +-------+-------------------------------+
        | 31    | System                        |
        +-------+-------------------------------+
        
    .. attribute:: value
    
        The raw value of the status register.
        
    '''

    @property
    def instructionSet(self):
        '''
        Get/set the processor's instruction set. These can be read from the
        :attr:`T` and :attr:`J` flags on the status.
        
        +-------+-----------------+
        | Value | Instruction set |
        +=======+=================+
        | 0     | ARM             |
        +-------+-----------------+
        | 1     | Thumb           |
        +-------+-----------------+
        | 2     | Jazelle         |
        +-------+-----------------+
        | 3     | ThumbEE         |
        +-------+-----------------+
        
        .. note:: The emulator does not support Jazelle mode due to lack of
                  documentation. Currently it treats Jazelle same as ARM. Also,
                  the emulator will not perform NULL checking in ThumbEE mode.
                  
        '''
        return self.J*2 + self.T
        
    @instructionSet.setter
    def instructionSet(self, newIS):
        self.J = newIS >> 1
        self.T = newIS & 1



FloatingPointStatus = BitPattern('NZCVQ_nFRRSS_LLLd__xuoeiD__XUOEI', rename={
    'Q': 'QC',
    'n': 'DN',
    'F': 'FZ',
    'R': 'RMode',
    'S': 'stride',
    'L': 'length',
    'd': 'IDE',
    'x': 'IXE',
    'u': 'UFE',
    'o': 'OFE',
    'e': 'DZE',
    'i': 'IOE',
    'D': 'IDC',
    'X': 'IXC',
    'U': 'UFC',
    'O': 'OFC',
    'E': 'DZC',
    'I': 'IOC',
}, className='FloatingPointStatus').returnType
'''
    This class represents the content of the floating-point status register for
    VFP and NEON.
    
    .. note::
    
        The emulator currently only checks the :attr:`N`, :attr:`Z`, :attr:`V`,
        :attr:`C`, and :attr:`QC` flags. All other flags are ignored. Floating
        point operations are done with the Python interpreter and uses the
        default rounding and exception control.
    
    .. attribute:: N
    
        Check/set the negative ("N") flag
    
    .. attribute:: Z
    
        Check/set the zero ("Z") flag
    
    .. attribute:: C
    
        Check/set the carry ("C") flag
    
    .. attribute:: V
    
        Check/set the overflow ("V") flag
    
    .. attribute:: QC
    
        Check/set the cumulative saturation ("QC") flag
    
    .. attribute:: DN
    
        Check/set the default NaN ("DN") control bit.
        
        +-------+-----------------------------------+
        | Value | Meaning                           |
        +=======+===================================+
        | 0     | Do not modify NaNs                |
        +-------+-----------------------------------+
        | 1     | Replace NaNs with the default one |
        +-------+-----------------------------------+
    
    .. attribute:: FZ
    
        Check/set whether flush-to-zero mode ("FZ") is enabled.
    
    .. attribute:: RMode
    
        Get/set the rounding Mode control field.
        
        +-------+------------------------+
        | Value | Round to               |
        +=======+========================+
        | 0     | Nearest (RN)           |
        +-------+------------------------+
        | 1     | Plus infinity (RP)     |
        +-------+------------------------+
        | 2     | Negative infinity (RM) |
        +-------+------------------------+
        | 3     | Zero (RZ)              |
        +-------+------------------------+
    
    .. attribute:: stride
    
        Get/set the vector stride field. (Deprecated)
    
    .. attribute:: length
    
        Get/set the vector length field. (Deprecated)
    
    .. attribute:: IDE
    
        Check/set if the Input Denormal exception trap ("IDE") is enabled.
    
    .. attribute:: IXE
    
        Check/set if the Inexact exception trap ("IXE") is enabled.
    
    .. attribute:: UFE
    
        Check/set if the Underflow exception trap ("UFE") is enabled.
    
    .. attribute:: OFE
    
        Check/set if the Overflow exception trap ("OFE") is enabled.
    
    .. attribute:: DZE
    
        Check/set if the Divide by Zero exception trap ("DZE") is enabled.
    
    .. attribute:: IOE
    
        Check/set if the Invalid Operation exception trap ("IOE") is enabled.
    
    .. attribute:: IDC
    
        Check/set the Input Denormal cumulative exception ("IDC") flag.
    
    .. attribute:: IXC
    
        Check/set the Inexact cumulative exception ("IXC") flag.
    
    .. attribute:: UFC
    
        Check/set the Underflow cumulative exception ("UFC") flag.
    
    .. attribute:: OFC
    
        Check/set the Overflow cumulative exception ("OFC") flag.
    
    .. attribute:: DZC
    
        Check/set the Divide by Zero cumulative exception ("DZC") flag.
    
    .. attribute:: IOC
    
        Check/set the Invalid Operation cumulative exception ("IOC") flag.
        
    .. attribute:: value
    
        The raw value of the status register.
'''


#if 'sphinx-build' in sys.argv[0]:
#    def status_init(self, value=16):
#        pass
#    def fpstat_init(self, value=0):
#        pass
#
#    Status.__init__ = status_init
#    FloatingPointStatus.__init__ = fpstat_init
#

if __name__ == '__main__':
    #     NZCVQttJ____ggggttttttEAIFTMMMMM
    s = 0b10110010000000001110100000110000 

    st = Status(s)
    assert st.N
    assert not st.Z
    assert st.C
    assert st.V
    assert not st.Q
    assert st.IT == 0b11101001
    assert not st.J
    assert st.GE == 0
    assert not st.E
    assert not st.A
    assert not st.F
    assert st.T
    assert st.M == 16
    assert st.value == s
    assert st.instructionSet == 1
    st.instructionSet = 2
    assert st.J
    assert not st.T
    assert st.N
    
