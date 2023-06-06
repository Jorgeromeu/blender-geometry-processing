import os
import sys

# Start blender with the plugin loaded
# usage:
# python start_blender.py BLENDER_PATH BLEND_FILE_PATH

# Jorge:   /usr/bin/blender
# Rodrigo: /Applications/Blender.app/Contents/MacOS/Blender
# Pavlos:  /snap/bin/blender

blender_executable_path = sys.argv[1]
blend_file_path = sys.argv[2]

os.system(f"{blender_executable_path} {blend_file_path}")
