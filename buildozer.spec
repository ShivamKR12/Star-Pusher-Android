[app]

# (str) Title of your application
title = Star Pusher

# (str) Package name
package.name = starpusher

# (str) Package domain (needed for android packaging)
package.domain = org.ShivamKR12

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,ogg,wav,mp3,ttf,otf,json,atlas,txt

# (str) Application versioning
version = 1.0

# (list) Application requirements
requirements = python3==3.10.12,hostpython3==3.10.12,pygame

# (str) Supported orientation (one of landscape, portrait or all)
orientation = landscape

# (bool) Indicate whether the screen should be fullscreen
fullscreen = 1

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android NDK API to use. Should be minimum API supported.
android.ndk_api = 21

# (list) The Android architectures to build for, can be: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (list) Permissions
android.permissions = INTERNET,VIBRATE
