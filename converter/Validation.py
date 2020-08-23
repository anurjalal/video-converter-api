
import os 
import re
import subprocess as sp
from config import UPLOAD_FOLDER

class Validation():
    
    def preset_validation(self, unique_path, ext, crf, fps):
        err = 0
        msg = ""
        if(unique_path == None or ""):
            msg = msg+(invalid_msg_template("path"))
            err+=1
        if(ext == None or ""):
            msg = msg+(invalid_msg_template("ext"))
            err+=1
        if(not re.match(r'\.',ext)):
            msg = msg+(invalid_msg_template("ext"))
            err+=1
        else:
            ext_without_dot = ext.split('.')[-1]
            if(not self.is_vid_format_valid(ext_without_dot)):
                msg = msg + f'video format is not accepted.'
                err+=1
            else:
                file_path = os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, unique_path))
                isPathExist = os.path.isfile(file_path)
                if(not isPathExist):
                    msg = msg + f'File location invalid. '
                    err+=1
        if(crf == None or ""):
            msg = msg+(invalid_msg_template("crf"))
            err+=1
        if(fps == None or ""):
            msg = msg+(invalid_msg_template("fps"))
            err+=1
        if(not fps.isnumeric()):
            msg = msg+ "fps should be a number. "
            err+=1
        if(not crf.isnumeric()):
            msg = msg+ "crf should be integer. "
            err+=1
        else:
            if(int(crf)<0 or int(crf)>51):
                msg = msg+ "fps should be in range 0-51. "
                err+=1
        return err,msg

    def invalid_msg_template(self, preset):
        return f'{preset} is invalid. '

    
    def is_vid_format_valid(self, ext_without_dot):
        cmd = ['ffmpeg', '-h' ,f'muxer={ext_without_dot}']
        process = sp.run(cmd, stdout=sp.PIPE)
        inv_messg = re.search("Unknown format+", str(process.stdout))
        if inv_messg:
            return False
        else:
            return True