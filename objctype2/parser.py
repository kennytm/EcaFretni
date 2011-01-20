#    
#    parser.py ... Objective-C type encoding parser
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

from objctype2.types import *
from balanced_substring import numericSubstring, balancedSubstring
import re

_primitive1c = frozenset([
    CLASS,
    NXATOM,
    SEL,
    BOOL_C99,
    UNSIGNED_CHAR,
    UNSIGNED_INT,
    UNSIGNED_LONG,
    UNSIGNED_LONG_LONG,
    UNSIGNED_SHORT,
    BOOL,
    CHAR,
    DOUBLE,
    FLOAT,
    INT,
    LONG,
    LONG_LONG,
    SHORT,
    VOID,
])

_modifier1c = frozenset([
    POINTER,
    COMPLEX,
    ONEWAY,
    CONST,
    BYCOPY,
    BYREF,
    IN,
    OUT,
    INOUT,
    GCINVISIBLE,
])

_objcRe = re.compile('"([^<"]+)?(?:<([^>]+)>)?"').match
_struMemRe = re.compile('"([^"]+)"').match

def decode(encoding):
    """
    Decode an encoded type string into an Objective-C type.
    
    This is equivalent to calling :func:`parse` with default parameters and
    discard the 2nd element of the returned tuple.
    """
    return parse(encoding)[0]
    


def parse(encoding, start=0, end=None, hasMemberName=True):
    """
    Parse an encoded type string into an Objective-C type.
    
    If you supply *start* and *end*, only the substring ``encoding[start:end]``
    will be parsed.
    
    Returns a tuple of :class:`~objctype2.types.Type` and the next index to
    parse. If nothing can be parsed, the type will become ``None``.
    
    Example::
    
        from objctype2.parser import parse
        from balanced_substring import numericSubstring
        
        typeinfo = 'c24@0:4@8@12{_NSRange=II}16'
        index = 0
        while True:
            (type_, index) = parse(typeinfo, index)
            if type_ is None:
                break
            (stackIndex, index) = numericSubstring(typeinfo, index)
            print (type_, '@', stackIndex)

        # prints:            
        #    Primitive('c') @ 24
        #    ObjCType() @ 0
        #    Primitive(':') @ 4
        #    ObjCType() @ 8
        #    ObjCType() @ 12
        #    Struct('_NSRange').append(Primitive('I')).append(Primitive('I')).freeze() @ 16

    """

    if end is None:
        end = len(encoding)

    if start >= end:
        return (None, end)
    
    firstChar = encoding[start]
    start += 1
    
    # primitives
    if firstChar in _primitive1c:
        return (Primitive(firstChar), start)
        
    # unary, or function pointer (^ and ^?)
    elif firstChar in _modifier1c:
        if start >= end or encoding[start] in "]})":
            return (Primitive(FUNCTION_POINTER), start)
        elif encoding[start] == '?':
            return (Primitive(FUNCTION_POINTER), start+1)
        else:
            (baseType, newStart) = parse(encoding, start, end, hasMemberName)
            return (Unary(firstChar, baseType), newStart)
    
    # char pointer
    elif firstChar == '*':
        return (Unary(POINTER, Primitive(CHAR)), start)
    
    # bitfield
    elif firstChar == 'b':
        (bitlen, newStart) = numericSubstring(encoding, start)
        return (Bitfield(bitlen), newStart)
    
    # array
    elif firstChar == '[':
        (length, newStart) = numericSubstring(encoding, start)
        (baseType, newNewStart) = parse(encoding, newStart, end, hasMemberName)
        assert encoding[newNewStart] == ']'
        return (Array(length, baseType), newNewStart+1)

    # objective-C type, or blocks
    elif firstChar == '@':
        if start >= end or encoding[start] not in '?"':
            return (ObjCType(), start)
        elif encoding[start] == '?':
            return (Primitive(BLOCK), start+1)
        else:
            # "foo"@"bar"@
            # "foo"@"NSObject""bar"@
            # "foo"@"bar"@"NSObject"
            m = _objcRe(encoding, start)
            if not m or (hasMemberName and m.end() < end and encoding[m.end()] not in '"]})'):
                return (ObjCType(), start)
            
            (name, protos) = m.groups()
            if protos:
                protos = protos.split(',')
            
            return (ObjCType(name, protos), m.end())
    
    # struct or union
    elif firstChar in '{(':
        isUnion = firstChar == '('
        newStart = start
        while encoding[newStart] not in '=)}':
            newStart = balancedSubstring(encoding, newStart)
        name = encoding[start:newStart]
        if encoding[newStart] == '=':
            newStart += 1
        stru = Struct(name, isUnion)
        while newStart <= end and encoding[newStart] not in ')}':
            hasMemberName = encoding[newStart] == '"'
            if hasMemberName:
                m = _struMemRe(encoding, newStart)
                memberName = m.group(1)
                newStart = m.end()
            else:
                memberName = None
            (baseType, newNewStart) = parse(encoding, newStart, end, hasMemberName)
            stru.append(baseType, memberName)
            newStart = newNewStart
        stru.freeze()
        return (stru, newStart+1)

if __name__ == '__main__':
    #    struct PairOfInt { int x; int y; };
    #    
    #    struct Foo {
    #    	float a;
    #    	float b;
    #    	float c;
    #    	_Complex float cf;
    #    	NSObject* obj;
    #    	int bf1 : 3;
    #    	int bf2 : 3;
    #    	int bf3 : 3;
    #    	int bf4 : 3;
    #    	int bf5 : 23;
    #    	int bf55 : 31;
    #    	int bf6 : 1;
    #    	BOOL bl;
    #    	char ch;
    #    	float fa[72];
    #    	struct PairOfInt rng;
    #    	int bf7 : 3;
    #    	_Complex float (*parr)[72];
    #    	float w;
    #    };


    encoding = '{Foo="a"f"b"f"c"f"cf"jf"obj"@"NSObject""bf1"b3"bf2"b3"bf3"b3"bf4"b3"bf5"b23"bf55"b31"bf6"b1"bl"c"ch"c"fa"[72f]"rng"{PairOfInt="x"i"y"i}"bf7"b3"parr"^[72jf]"w"f}'
    stru = Struct('Foo')
    stru.append(Primitive(FLOAT), 'a')
    stru.append(Primitive(FLOAT), 'b')
    stru.append(Primitive(FLOAT), 'c')
    stru.append(Unary(COMPLEX, Primitive(FLOAT)), 'cf')
    stru.append(ObjCType("NSObject"), 'obj')
    stru.append(Bitfield(3), 'bf1')
    stru.append(Bitfield(3), 'bf2')
    stru.append(Bitfield(3), 'bf3')
    stru.append(Bitfield(3), 'bf4')
    stru.append(Bitfield(23), 'bf5')
    stru.append(Bitfield(31), 'bf55')
    stru.append(Bitfield(1), 'bf6')
    stru.append(Primitive(BOOL), 'bl')
    stru.append(Primitive(CHAR), 'ch')
    stru.append(Array(72, Primitive(FLOAT)), 'fa')
    stru.append(Struct('PairOfInt').append(Primitive(INT), 'x').append(Primitive(INT), 'y').freeze(), 'rng')
    stru.append(Bitfield(3), 'bf7')
    stru.append(Unary(POINTER, Array(72, Unary(COMPLEX, Primitive(FLOAT)))), 'parr')
    stru.append(Primitive(FLOAT), 'w')
    stru.freeze()
    
    assert parse(encoding) == (stru, len(encoding))
    assert decode(encoding) == stru
    
    #    struct WebStringDebugger {
    #        /*funcptr*/ void** field1;
    #        struct HashSet<JSC::JSGlobalObject*,WTF::PtrHash<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*> > {
    #            struct HashTable<JSC::JSGlobalObject*,JSC::JSGlobalObject*,WTF::IdentityExtractor<JSC::JSGlobalObject*>,WTF::PtrHash<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*> > {
    #                struct JSGlobalObject** m_table;
    #                int m_tableSize;
    #                int m_tableSizeMask;
    #                int m_keyCount;
    #                int m_deletedCount;
    #            } m_impl;
    #        } field2;
    #        bool field3;
    #        struct RetainPtr<WebScriptCallFrame> {
    #            /*objc*/ WebScriptCallFrame* m_ptr;
    #        } field4;
    #        struct ProtectedPtr<JSC::JSGlobalObject> {
    #            struct JSGlobalObject* m_ptr;
    #        } field5;
    #        struct RetainPtr<WebScriptCallFrame> {
    #            /*objc*/ WebScriptCallFrame* m_ptr;
    #        } field6;
    #    }* foo;
    encoding = '^{WebScriptDebugger=^^?{HashSet<JSC::JSGlobalObject*,WTF::PtrHash<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*> >="m_impl"{HashTable<JSC::JSGlobalObject*,JSC::JSGlobalObject*,WTF::IdentityExtractor<JSC::JSGlobalObject*>,WTF::PtrHash<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*> >="m_table"^^{JSGlobalObject}"m_tableSize"i"m_tableSizeMask"i"m_keyCount"i"m_deletedCount"i}}B{RetainPtr<WebScriptCallFrame>="m_ptr"@"WebScriptCallFrame"}{ProtectedPtr<JSC::JSGlobalObject>="m_ptr"^{JSGlobalObject}}{RetainPtr<WebScriptCallFrame>="m_ptr"@"WebScriptCallFrame"}}'
    res = Unary(POINTER, Struct('WebScriptDebugger')
        .append(Unary(POINTER, Primitive(FUNCTION_POINTER)))
        .append(Struct('HashSet<JSC::JSGlobalObject*,WTF::PtrHash<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*> >')
            .append(Struct('HashTable<JSC::JSGlobalObject*,JSC::JSGlobalObject*,WTF::IdentityExtractor<JSC::JSGlobalObject*>,WTF::PtrHash<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*>,WTF::HashTraits<JSC::JSGlobalObject*> >')
                .append(Unary(POINTER, Unary(POINTER, Struct('JSGlobalObject').freeze())), 'm_table')
                .append(Primitive(INT), 'm_tableSize')
                .append(Primitive(INT), 'm_tableSizeMask')
                .append(Primitive(INT), 'm_keyCount')
                .append(Primitive(INT), 'm_deletedCount')
            .freeze(), 'm_impl')
        .freeze())
        .append(Primitive(BOOL_C99))
        .append(Struct('RetainPtr<WebScriptCallFrame>')
            .append(ObjCType('WebScriptCallFrame'), 'm_ptr')
        .freeze())
        .append(Struct('ProtectedPtr<JSC::JSGlobalObject>')
            .append(Unary(POINTER, Struct('JSGlobalObject').freeze()), 'm_ptr')
        .freeze())
        .append(Struct('RetainPtr<WebScriptCallFrame>')
            .append(ObjCType('WebScriptCallFrame'), 'm_ptr')
        .freeze())
    .freeze())
    assert parse(encoding) == (res, len(encoding))
    
    #    template <char c='='>
    #    Foo {
    #        int x;
    #    };
    encoding = ''':){Foo<'='>="x"i}:)'''
    res = Struct("Foo<'='>").append(Primitive(INT), 'x').freeze()
    assert parse(encoding, 2) == (res, len(encoding)-2)
    
    encoding = '(?=*^)'
    res = Struct(isUnion=True).append(Unary(POINTER, Primitive(CHAR))).append(Primitive(FUNCTION_POINTER)).freeze()
    assert decode(encoding) == res
    
    encoding = '{?={?="foo"@"bar"@}{?="foo"@"bar"@"baz"}{?=@"bar"@"baz"}@?}'
    res = Struct().append(Struct()
        .append(ObjCType(), 'foo')
        .append(ObjCType(), 'bar')
    .freeze()).append(Struct()
        .append(ObjCType(), 'foo')
        .append(ObjCType('baz'), 'bar')
    .freeze()).append(Struct()
        .append(ObjCType('bar'))
        .append(ObjCType('baz'))
    .freeze()).append(Primitive(BLOCK)).freeze()
    assert decode(encoding) == res
    
    assert decode('@"<Blah,Blah,Foo>"') == ObjCType(protocols=['Foo', 'Blah'])
    assert decode('@"NSObject<Foo>"') == ObjCType(name='NSObject', protocols=['Foo'])
    
    (bt, idx) = parse("?", 1)
    assert bt is None 
    assert idx == 1
