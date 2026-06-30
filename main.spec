# -*- mode: python ; coding: utf-8 -*-
import os


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('frontend/dist', 'frontend/dist')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Filter out system GUI/GNOME libraries from the PyInstaller bundle.
# This forces the compiled executable to load GTK, GDK, WebKit, Pango, and Cairo
# dynamically from the host Linux system where theme and icon databases (like Breeze/SVG)
# are properly configured, preventing GTK missing-icon asset crashes.
excluded_libs = {
    'libgtk-3', 'libgdk-3', 'libgdk_pixbuf-2.0', 'libwebkit2gtk-4.0', 'libwebkit2gtk-4.1',
    'libjavascriptcoregtk-4.0', 'libjavascriptcoregtk-4.1', 'libsoup-2.4', 'libsoup-3.0',
    'libgio-2.0', 'libglib-2.0', 'libgobject-2.0', 'libgmodule-2.0', 'libharfbuzz',
    'libpango-1.0', 'libpangocairo-1.0', 'libcairo', 'libcairo-gobject'
}
a.binaries = [x for x in a.binaries if not any(lib in x[0].lower() or lib in x[1].lower() for lib in excluded_libs)]

# Filter out PyInstaller runtime hooks that configure GTK/GDK temp paths
excluded_hooks = {'pyi_rth_gtk', 'pyi_rth_gdkpixbuf', 'pyi_rth_gi', 'pyi_rth_glib', 'pyi_rth_gio'}
a.scripts = [x for x in a.scripts if not any(h in x[0].lower() or h in x[1].lower() for h in excluded_hooks)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
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
    icon=['assets/app_icon.ico'],
)
