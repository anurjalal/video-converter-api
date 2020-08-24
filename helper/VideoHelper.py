from datetime import datetime
import os
from werkzeug.utils import secure_filename
import uuid

class VideoHelper():
    
    def __init__(self, filehelper):
        self._filehelper = filehelper

    def generateDailyFolder(self, upload_base_path):
        curr_time = datetime.now()
        today_str = curr_time.strftime("%d-%m-%Y")
        if(os.path.isdir(os.path.abspath(os.path.join(os.getcwd(), upload_base_path, today_str))) is not True):
            try:
                os.mkdir(os.path.abspath(os.path.join(os.getcwd(), upload_base_path, today_str)))
            except OSError as exc:
                print(exc.args)
        return os.path.abspath(os.path.join(os.getcwd(), upload_base_path, today_str))

    def generateUploadPathname(self, base_path):
        curr_time = datetime.now()
        millis_str = curr_time.strftime("%H:%M:%S")
        s_filename = secure_filename(self._filehelper.get_filename())
        s_filename, ext = os.path.splitext(s_filename)
        unique_filename = f'{millis_str}_{uuid.uuid4()}_{s_filename}{self._filehelper.get_ext()}'
        path = os.path.abspath(os.path.join(base_path, unique_filename))
        return path

    def generateConvertedPathname(self , preset_ext, out_base_path):
        filename = self._filehelper.get_filename()
        s_filename = secure_filename(filename)
        unique_filename = f'{s_filename}{preset_ext}'
        path = os.path.abspath(os.path.join(os.getcwd(), out_base_path, unique_filename))
        return path