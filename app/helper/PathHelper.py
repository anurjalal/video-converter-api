
import os

class PathHelper():
    
    def __init__(self, abs_path):
        self._abs_path = abs_path

    def get_simple_directory(self):
        s_directory = os.path.basename(os.path.normpath(os.path.dirname(self._abs_path)))
        return s_directory