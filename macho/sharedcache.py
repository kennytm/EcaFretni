#    
#    sharedcache.py ... Parse file from the dyld_shared_cache
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

from .macho import MachOError, MachO
from mmap import mmap, ACCESS_READ
from .utilities import peekFixedLengthString, peekStruct, peekStructs, peekString
from struct import Struct
from .arch import Arch
from data_table import DataTable
from .vmaddr import Mapping, MappingSet
import os
from os.path import basename, splitext


class DyldSharedCache(object):
    '''Represents a shared cache file (``dyld_shared_cache_XXX``).
    
    The dyld shared cache is an optimization mechanism introduced in Mac OS X 
    10.6 and iPhone OS 3.1. All system libraries of the active architecture will
    be analyzed and collected into a single file. In this way, the dynamic
    library loader (``dyld``) only needs to map the whole cache file to memory,
    instead of finding the hundreds of them one by one. 
    
    The endianness will be guessed from the architecture this cache is created 
    on. A :exc:`~macho.macho.MachOError` will be raised if there is no such
    information. You could supply the *endian* (big ``'>'`` or little ``'<'``)
    if you can obtain this from more reliable source.
    
    Example code::
    
        from macho.sharedcache import DyldSharedCache
        import macho.features
        macho.features.enable('symbol')
        
        path = '/Volumes/Jasper8C148.K48OS/System/Library/Caches/com.apple.dyld/dyld_shared_cache_armv7'
        with DyldSharedCache(path) as sc:
            uikit = sc.images.any1('name', 'UIKit').machO
            for s in uikit.symbols:
                print(s.name)
    
    
    .. attribute:: file
    
        The :class:`~mmap.mmap` object of this shared cache.
    
    .. attribute:: filename
    
        File name of this shared cache
    
    .. attribute:: endian
    
        Return the (guessed) endianness of this shared cache.
		
		+--------------+------------+
		| Return value | Endianness |
		+==============+============+
		| ``'>'``      | Big        |
		+--------------+------------+
		| ``'<'``      | Little     |
		+--------------+------------+

    .. attribute:: arch
    
        Return the architecture (an :class:`~macho.arch.Arch` instance) of this
        shared cache.
        
    .. attribute:: mappings
    
        A list of :class:`Mapping`\s of this shared cache.
    
    .. attribute:: images
    
        A :class:`~data_table.DataTable` of :class:`Image`\s in this shared
        cache with the following columns:
        
        * ``'address'`` (unique, integer, the VM address to this image)
        
        * ``'name'`` (unique, string, the filename of this image after deleting
          all extensions, e.g. 'UIKit' or 'libxml2'.)

    '''
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        return self.close(exc_type, exc_value, traceback)
    
    def __init__(self, filename, endian=None):
        self.filename = filename
        self.fileno = -1
        self.file = None
        self.endian = endian
        self.arch = None
        
    def open(self):
        """Open the shared cache file object for access.
        
        .. note:: You should use the :keyword:`with` statement instead of
                  calling this method explicitly.
        """
        if self.file is None:
            flag = os.O_RDONLY | getattr(os, 'O_BINARY', 0)
            fileno = os.open(self.filename, flag)
            self.fileno = fileno
            self.file = mmap(fileno, 0, access=ACCESS_READ)
        else:
            self.file.seek(0)
        self.__analyze()

    def close(self, exc_type=None, exc_value=None, traceback=None):
        """Close the shared cache file object.
        
        .. note:: You should use the :keyword:`with` statement instead of calling
                  this method explicitly.
        
        """
        if self.file is not None:
            self.file.close()
            self.file = None
        if self.fileno >= 0:
            os.close(self.fileno)
            self.fileno = -1
        
    
    def __analyze(self):
        magic_string = peekFixedLengthString(self.file, 15, position=0)
        (magic, archname) = magic_string.split()
        if magic != 'dyld_v1':
            raise MachOError('Invalid magic "{0}"'.format(magic_string))
        
        self.arch = Arch(archname)
        if self.endian is None:
            self.endian = self.arch.endian
            if self.endian is None:
                raise MachOError('Cannot guess endian from architecture "{0}"'.format(archname))
        
        (mappingOffset, mappingCount, imagesOffset, imagesCount, self.dyldBaseAddress) = \
            peekStruct(self.file, Struct(self.endian + '4LQ'), position=16)
            
        self.mappings = MappingSet(self.__analyzeMappings(mappingOffset, mappingCount))
        self.mappings.freeze()
        
        images = DataTable('!address', '!name')
        for image in self.__analyzeImages(imagesOffset, imagesCount):
            bn = basename(image.path);
            while True:
                (stem, ext) = splitext(bn)
                if not ext:
                    break
                bn = stem
                
            images.append(image, address=image.address, name=bn)
            
        self.images = images
        
    
    def __analyzeMappings(self, offset, count):
        mappings = peekStructs(self.file, Struct(self.endian + '3Q2L'), count, position=offset)
        return (Mapping(*content) for content in mappings)
    
    
    def __analyzeImages(self, offset, count):
        images = peekStructs(self.file, Struct(self.endian + '3Q2L'), count, position=offset)
        f = self.file
        image_for_address = {}
        
        for i, (address, modTime, inode, pathFileOffset, pad) in enumerate(images):
            path = peekString(f, position=pathFileOffset)
            if address in image_for_address:
                image = image_for_address[address]
                image.symlinks.append(path)
            else:
                image = Image(address, modTime, inode, path, pad)
                image.cache = self
                image.index = i
                image_for_address[address] = image
            yield image
            
                        


class Image(object):
    '''This class represents an image (a Mach-O file) in a shared cache.
    
    .. attribute:: address
    
        The VM address this image should be mapped to.
    
    .. attribute:: modtime
    
        The timestamp when the image is modified.
    
    .. attribute:: inode
        
        The inode of the image.
    
    .. attribute:: path
    
        The primary path of the image.
    
    .. attribute:: symlinks
    
        A list of paths that should be symbolically linked to this image also.
    
    .. attribute:: pad
    
        Unknown.
    
    .. attribute:: cache
    
        The :class:`DyldSharedCache` object that stores this image.
    
    .. attribute:: index
    
        The index to the image's shared cache file.
    
    '''
    
    def __init__(self, address, modtime, inode, path, pad):
        self.address = address
        self.modtime = modtime
        self.inode = inode
        self.path = path
        self.symlinks = []
        self.pad = pad
        self._machO = None
        self.cache = None
        self.index = -1
    
    @property
    def machO(self):
        '''
        Return an opened :class:`~macho.macho.MachO` object associated with
        this image.
        
        This object's content is weak-referenced from its shared cache file, 
        therefore, you need to ensure that the shared cache file is open as long
        as you need to read from this object.
        '''
        if self._machO is None:
            cache = self.cache
            mo = MachO(self.path, cache.arch)
            mo.cache = cache
            mo.mappings = cache.mappings
            mo.openWith(cache.file, cache.mappings.fromVM(self.address))
            self._machO = mo
        return self._machO

    def __str__(self):
        return "<Image [{0}] @ 0x{1:x}>".format(self.path, self.address)




