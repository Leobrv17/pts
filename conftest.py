import sys
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(root_dir, 'app')
sys.path.extend([root_dir, app_dir])
