# This mod continously flushes python.log allowing you to 'tail' the log file in near real-time.
# Install instructions:
# 1. compile the script:
#     $ python -m py_compile log_flusher_mod.py
# 2. copy log_flusher_mod.pyc to game's res_mods\0.9.8.1\scripts\client\mods -folder
#    (it is expected here that you have other mods already installed with
#     CameraNode.pyc and rest of other stuff).
# 3. Download and extract GNU Windows 32 core utils from:
#     http://gnuwin32.sourceforge.net/downlinks/coreutils-bin-zip.php
# 4. Put the contained bin-folder to your PATH environment variable
# 5. Open command prompt and run:
#     $ tail -f path\to\python.log
#

import game
game.autoFlushPythonLog()
