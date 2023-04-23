# -*- mode: python -*-

block_cipher = None

additionalLibs = []
#additionalLibs.append( ("libGL.so.1", "/usr/lib64/libGL.so.1", 'BINARY') )

import os

path=os.environ['HOME'] + '/artisan-master/src'
if not os.path.isdir(path):
    path=os.environ['HOME'] + '/artisan/src'
# For Travis
if not os.path.isdir(path):
    path=os.getcwd()

a = Analysis(['artisan.py'],
             pathex=[path],
             binaries=[],
             datas=[],
             hiddenimports=['charset_normalizer.md__mypyc', # part of requests 2.28.2 # see https://github.com/pyinstaller/pyinstaller-hooks-contrib/issues/534
                            'scipy.spatial.transform._rotation_groups',
                            'scipy._lib.messagestream',
                            'scipy.special.cython_special',
                            'matplotlib.backends.backend_pdf',
                            'matplotlib.backends.backend_svg',
                            'pkg_resources.py2_warn'
                            ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

# Remove pyi_rth_mplconfig.py useless because it makes our startup slow.
# This hook only applies to one-file distributions.
for s in a.scripts:
    if s[0] == 'pyi_rth_mplconfig':
        a.scripts.remove(s)
        break

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='artisan',
          debug=False,
          strip=False,
          upx=True,
          console=True )

coll = COLLECT(exe,
               a.binaries + additionalLibs,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='artisan')
