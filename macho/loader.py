#    
#    loader.py ... Load Mach-O file with specified path
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

from .macho import MachO
from .arch import Arch
from .sharedcache import DyldSharedCache
from contextlib import contextmanager
from os.path import join, isfile, sep, altsep

__fnmethods = [
    join,
    lambda sdk, fn: join(sdk, 'System', 'Library', 'Frameworks', fn+'.framework', fn),
    lambda sdk, fn: join(sdk, 'System', 'Library', 'PrivateFrameworks', fn+'.framework', fn),
    lambda sdk, fn: join(sdk, 'usr', 'lib', fn+'.dylib'),
    lambda sdk, fn: join(sdk, 'Applications', fn+'.app', fn),
    lambda sdk, fn: join(sdk, 'System', 'Library', 'CoreServices', fn+'.app', fn),
]

def __stripLeadingSep(fn):
    seps = sep
    if altsep:
        seps += altsep
    return fn.lstrip(seps)


def _loadFile(filename, sdk, cache_images_any, arch, lenientArchMatching):
    if cache_images_any:
        image = cache_images_any('path', filename)
        if image:
            return image.machO
        image = cache_images_any('name', filename)
        if image:
            return image.machO

    strippedFilename = __stripLeadingSep(filename)
    for f in __fnmethods:
        fn = f(sdk, filename)
        if isfile(fn):
            break
    else:
        fn = filename
    
    return MachO(fn, arch, lenientArchMatching).__enter__()



class MachOLoader(object):
    '''Loads multiple :class:`~macho.macho.MachO` object from Mach-O files or 
    images in a shared cache by filename.
    
    Example::
    
        with MachOLoader('AudioToolbox', 'CoreMedia', cache='', sdk='/Volumes/Jasper8C148.N90OS/') \\
                as (audioToolbox, coreMedia):
            ...
    
    This class supports the following keywoard arguments in the initializer:
    
    :param cache: The path, or a :class:`~macho.sharedcache.DyldSharedCache`
        object which the loader may load from. If you pass a
        :class:`~macho.sharedcache.DyldSharedCache`, it should be already
        :meth:`~macho.sharedcache.DyldSharedCache.open`\ ed.
    :param sdk: The root folder which the files are searched. Default to ``'/'``.
    :param arch: The :class:`~macho.arch.Arch` the images should be in. Default
        to ``'armv7'``.
    :param lenientArchMatching: Whether arch-matching should be done leniently
        (will not affect images loaded from *cache*)
    :param endian: Specify endianness of the *cache*.
    
    The cache file, if not ``None``, is loaded by the following means in order:
    
    1. If *cache* is a :attr:`~macho.sharedcache.DyldSharedCache`, use it
       directly.
    2. If *cache* is an empty string, load from
       ``<sdk>/System/Library/Caches/com.apple.dyld/dyld_shared_cache_<arch>``
    3. Otherwise, load from ``<sdk>/<cache>`` if exists.
    
    4. Load from ``<cache>``.
    
    The files are loaded from the following means in order:
    
    1. An image matched by ``'path'`` in the *cache*'s
       :attr:`~macho.sharedcache.DyldSharedCache.images`.
    2. An image matched by ``'name'`` in the *cache*'s
       :attr:`~macho.sharedcache.DyldSharedCache.images`.
    3. The file ``<sdk>/<filename>`` if exists.
    4. The file ``<sdk>/System/Library/Frameworks/<filename>.framework/<filename>``
       if exists.
    5. The file ``<sdk>/System/Library/PrivateFrameworks/<filename>.framework/<filename>``
       if exists.
    6. The file ``<sdk>/usr/lib/<filename>.dylib`` if exists.
    7. The file ``<sdk>/Applications/<filename>.app/<filename>`` if exists.
    8. The file ``<sdk>/System/Library/CoreServices/<filename>.app/<filename>``
       if exists.
    
    9. The file ``<filename>``.
    
    '''
    
    def __init__(self, *filenames, **kwargs):
        kg = kwargs.get
        arch = Arch(kg('arch', 'armv7'))
        sdk = kg('sdk', '/')
        self._sdk = sdk
        self._arch = arch
        self._filenames = filenames
    
        cache = kg('cache')
        if cache is not None:
            if isinstance(cache, DyldSharedCache):
                cachePath = None
            elif cache == '':
                cachePath = join(sdk, 'System/Library/Caches/com.apple.dyld/dyld_shared_cache_' + str(arch))
            else:
                cachePath = join(sdk, cache.lstrip('/'))
                if not isfile(cachePath):
                    cachePath = cache
            if cachePath:
                cache = DyldSharedCache(cachePath, endian=kg('endian')).__enter__()

        self._cache = cache
        self._lenientArchMatching = kg('lenientArchMatching', False)
        self._openedMachOs = [None] * len(filenames)
    
    def __enter__(self):
        cache = self._cache
        sdk = self._sdk
        cache_images_any = cache.images.any if cache else None
        arch = self._arch
        lenientArchMatching = self._lenientArchMatching
        
        machOs = self._openedMachOs
        try:
            for i, fn in enumerate(self._filenames):
                machOs[i] = _loadFile(fn, sdk, cache_images_any, arch, lenientArchMatching)
        finally:
            return machOs

    def __exit__(self, exc_type, exc_value, traceback):
        for mo in self._openedMachOs:
            if mo:
                mo.__exit__(exc_type, exc_value, traceback)


