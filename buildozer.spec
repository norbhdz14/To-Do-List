[app]
title = Lista de tareas
package.name = listadetareas
package.domain = org.cipher

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0
requirements = python3,kivy

# --- LÍNEA PARA EVITAR EL ERROR DE CPYTHON ---
p4a.branch = master

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/logo.png

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
