[app]
title = Crypto Live Market
package.name = cryptolivemarket
package.domain = com.vbhuvad
source.dir = .
source.include_exts = py,kv,png,jpg,json
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 35
android.minapi = 24
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
p4a.fork = kivy
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
