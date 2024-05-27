from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = collect_submodules('qutip')
binaries = collect_data_files('qutip', subdir='core/cy')

