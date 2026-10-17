[app]
title = Crypto Dashboard
package.name = cryptodashboard
package.domain = org.example
source.dir = .
source.include_exts = py
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 35
android.minapi = 24
android.accept_sdk_license = True
p4a.fork = kivy
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
