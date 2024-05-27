# -*- mode: python ; coding: utf-8 -*-
import platform


block_cipher = None


a = Analysis(
    ['quasi/gui/main.py'],
    pathex=['.'],
    binaries=[],
    
    datas=[
        ('quasi/gui/assets/*', 'quasi/gui/assets'), 
        ('wheels/linux/*.whl', 'wheels/linux'),  # Linux wheels
        ('wheels/windows/*.whl', 'wheels/windows') # Windows wheels
    ], 
    hiddenimports=[
        'numpy', 'numba', 'scipy', 'flet', 'matplotlib', 'qutip', 
        'seaborn', 'plotly', 'jinja2', 'mpmath', 'toml', 
        'scipy.special._ufuncs', 'scipy.special._cdflib',
        'photon_weave'
    ], 
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
os_name = platform.syste().lower()
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
wheel_path = 'wheels/windows' if os_name == 'windows' else 'wheels/linux'
a.datas += [(f'{wheel_path}/*.whl', 'wheels')]

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QuaSi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='quasi/gui/assets/icon/quasi_icon.ico'
)
