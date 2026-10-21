[app]
title = Lista de tareas
package.name = listadetareas
package.domain = org.cipher

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0
requirements = python3,kivy

# Usar una etiqueta estable oficial de python-for-android
p4a.branch = v2024.01.21

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
