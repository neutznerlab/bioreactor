import PyInstaller.__main__

PyInstaller.__main__.run([
    'modelRunnerClass.py',
    '--onedir',
    '--console',
    '-y'
])