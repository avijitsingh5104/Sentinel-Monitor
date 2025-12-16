# welcome_anim_runner.py
import sys
import os

# ensure current dir is the script dir (helps when launched from anywhere)
script_dir = os.path.abspath(os.path.dirname(__file__))
os.chdir(script_dir)

from animations import WelcomeOverlay

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "User"
    WelcomeOverlay(name).show()
