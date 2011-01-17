#    
#    features.py ... Enable features in Mach-O
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


"""
By default, the :mod:`macho.macho` module does have many features, and the
interesting ones are delegated to the load command parsers, which the developers
must import them to enable. This module defines the convenient function
:meth:`enable` to formalize the process. 
"""


def _enable_libord():
    import macho.loadcommands.dylib

def _enable_vmaddr():
    import macho.loadcommands.segment

def _enable_symbol():
    import macho.symbol
    import macho.loadcommands.symtab
    import macho.loadcommands.dysymtab
    import macho.loadcommands.dyld_info
    import macho.sections.symbol_ptr

def _enable_encryption():
    import macho.loadcommands.encryption_info

def _enable_strings():
    import macho.sections.cstring
    import macho.sections.cfstring

def _enable_objc():
    import macho.sections.objc.classlist
    import macho.sections.objc.protolist
    import macho.sections.objc.catlist

def _enable_all():
    _enable_symbol()
    _enable_vmaddr()
    _enable_encryption()
    _enable_libord()
    _enable_strings()

__features = {
    'libord': _enable_libord,
    'symbol': _enable_symbol,
    'vmaddr': _enable_vmaddr,
    'encryption': _enable_encryption,
    'objc': _enable_objc,
    'all': _enable_all,
}


def enable(*features):
    '''Enable features.
    
    Currently, the following features are supported:
    
    +------------------+-------------------------------------------------+--------------------------------------------+
    | Feature          | Purpose                                         | Modules imported                           |
    +==================+=================================================+============================================+
    | ``'libord'``     | Finding a                                       | :mod:`macho.loadcommands.dylib`            |
    |                  | :class:`~macho.loadcommands.dylib.DylibCommand` |                                            |
    |                  | from the library ordinal.                       |                                            |
    +------------------+-------------------------------------------------+--------------------------------------------+
    | ``'vmaddr'``     | Convert VM addresses to and from file offsets.  | :mod:`macho.loadcommands.segment`          |
    +------------------+-------------------------------------------------+--------------------------------------------+
    | ``'symbol'``     | Retrieve :class:`~sym.Symbol`\s of the file.    | :mod:`macho.symbol`,                       |
    |                  |                                                 | :mod:`macho.loadcommands.symtab`,          |
    |                  |                                                 | :mod:`macho.loadcommands.dysymtab`,        |
    |                  |                                                 | :mod:`macho.loadcommands.dyld_info`,       |
    |                  |                                                 | :mod:`macho.sections.symbol_ptr`           |
    +------------------+-------------------------------------------------+--------------------------------------------+
    | ``'encryption'`` | Checking if a location is encrypted.            | :mod:`macho.loadcommands.encryption_info`  |
    +------------------+-------------------------------------------------+--------------------------------------------+
    | ``'strings'``    | Retrieve string constants (as                   | :mod:`macho.sections.cstring`,             |
    |                  | :class:`~sym.Symbol`\s) of the file.            | :mod:`macho.sections.cfstring`             |
    +------------------+-------------------------------------------------+--------------------------------------------+
    | ``'objc'``       | Parse Objective-C structures.                   | :mod:`macho.sections.objc.classlist`,      |
    |                  |                                                 | :mod:`macho.sections.objc.protolist`,      |
    |                  |                                                 | :mod:`macho.sections.objc.catlist`         |
    +------------------+-------------------------------------------------+--------------------------------------------+
    | ``'all'``        | Turn on all the above features                                                               |
    +------------------+----------------------------------------------------------------------------------------------+

    Once a feature is enabled, it cannot be disabled later. Note that some
    features depends on others to work, so turn it on will implicitly import
    their dependency as well. For instance, using the ``'symbol'`` feature will
    make ``'vmaddr'`` and ``'libord'`` also available.
    
    If an unrecognized feature is provided, it will be ignored.

    '''
    for feature in features:
        if feature in __features:
            __features[feature]()

