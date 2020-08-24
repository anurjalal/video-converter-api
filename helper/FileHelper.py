import os


class FileHelper:

    def __init__(self, filename):
        self._filename = filename

    def get_filename(self):
        return self._filename

    def get_ext(self):
        _, ext = os.path.splitext(self._filename)
        return ext

    def get_filename_modifiers(self):
        filename_modifiers, _ = os.path.splitext(self._filename)
        return filename_modifiers

    def get_ext_without_dot(self):
        ext_without_dot = self.get_ext().replace('.', '')
        return ext_without_dot
