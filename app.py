import os
import logging
import uuid
import subprocess as sp
import re
from datetime import datetime
from config import UPLOAD_FOLDER, RESULT_FOLDER, REDIS_URL, SECRET_KEY
from flask import Flask, request, abort, jsonify, session, send_from_directory, Response
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from celery import Celery, Task
from celery_config import make_celery
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)
celery = make_celery(app)
logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)

app.secret_key = SECRET_KEY

class Video():
    def __init__(self, filename):  
        self.name = name

@app.before_first_request
def before_first_request_func():
    session["upload_filename"] = []

@app.route('/upload', methods=['POST'])
def upload():
    """Upload file endpoint."""
    if request.method == 'POST':
        if not request.files.get('file', None):
            err_mssg = "invalid request. "
            return abort(Response(err_mssg, 400))
        received_file = request.files['file']
        _, ext = os.path.splitext(received_file.filename)
        file_helper = FileHelper(received_file.filename)
        video_helper = VideoHelper(file_helper)
        ext_without_dot = file_helper.get_ext_without_dot()
        upload_validator = Validation()
        if(not upload_validator.is_vid_format_valid(ext_without_dot)):
            err_mssg = f'video format of {received_file.filename} is not accepted.'
            return abort(Response(err_mssg, 400))
        daily_folder = video_helper.generateDailyFolder(UPLOAD_FOLDER)
        out_path = video_helper.generateUploadPathname(daily_folder)
        uploader = VideoUploader(received_file, out_path)
        if(uploader.saveFile()):
            data = os.path.join(PathHelper(out_path).get_simple_directory(), os.path.basename(out_path))
            session_key = "upload_filename"
            uploader.update_cookies(session_key, data)
            return jsonify({
            'success': True,
            'message': f'the file {received_file.filename} has been successfully uploaded'
            })
        err_mssg = f'the file {received_file.filename} failed to upload'
        abort(Response(err_mssg, 400))

@celery.task()
def video_converter(unique_path, ext, crf, fps):
    err = 0
    in_path = os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, unique_path))
    file_helper = FileHelper(unique_path)
    out_path = VideoHelper(file_helper).generateConvertedPathname(ext, RESULT_FOLDER)
    converter = VideoConverter(in_path,out_path)
    err = 0
    if(converter.convert(ext,crf,fps)):
        return err, out_path
    else:
        err = 1
        return err, "failed to convert. "

@app.route('/converter', methods=['GET'])
def get_converter():
    if request.method == 'GET':
        unique_path = request.args.get('unique_path')
        ext = request.args.get('ext')
        crf = request.args.get('crf')
        fps = request.args.get('fps')
        converter_validator = Validation()
        err_validation, msg_validation = converter_validator.preset_validation(unique_path, ext,crf, fps)
        if(err_validation>0):
            abort(Response(msg_validation, 400))
        task = video_converter.delay(unique_path, ext, crf, fps)
        async_result = AsyncResult(id=task.task_id, app=celery)
        err, msg = async_result.get()
        if(err != 0):
            return abort(Response(msg, 400))
        else:
            return send_from_directory(os.path.dirname(msg), os.path.basename(msg))

@app.route('/upload_path', methods=['GET'])
def get():
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': session.get("upload_filename")
            })

class FileHelper():
    def __init__(self, filename):
        self._filename = filename

    def get_filename(self):
        return self._filename

    def get_ext(self):
        _ , ext = os.path.splitext(self._filename)
        return ext

    def get_filename_modifiers(self):
        filename_modifiers, _ = os.path.splitext(self._filename)
        return filename_modifiers

    def get_ext_without_dot(self):
         ext_without_dot = self.get_ext().replace('.', '')
         return ext_without_dot

class PathHelper():
    def __init__(self, abs_path):
        self._abs_path = abs_path

    def get_simple_directory(self):
        s_directory = os.path.basename(os.path.normpath(os.path.dirname(self._abs_path)))
        return s_directory

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
                logger.info(exc.args)
        return os.path.abspath(os.path.join(os.getcwd(), upload_base_path, today_str))

    def generateUploadPathname(self, base_path):
        curr_time = datetime.now()
        millis_str = curr_time.strftime("%H:%M:%S")
        s_filename = secure_filename(self._filehelper.get_filename())
        s_filename, ext = os.path.splitext(s_filename)
        unique_filename = f'{millis_str}_{uuid.uuid4()}_{s_filename}{self._filehelper.get_ext()}'
        logger.info(str(unique_filename))
        path = os.path.abspath(os.path.join(base_path, unique_filename))
        return path

    def generateConvertedPathname(self , preset_ext, out_base_path):
        filename = self._filehelper.get_filename()
        s_filename = secure_filename(filename)
        unique_filename = f'{s_filename}{preset_ext}'
        path = os.path.abspath(os.path.join(os.getcwd(), out_base_path, unique_filename))
        return path

class VideoConverter():
    def __init__(self, abs_in_path, abs_out_path):
        self._abs_in_path = abs_in_path
        self._abs_out_path = abs_out_path

    def convert(self, ext, crf, fps):
        command = ['ffmpeg', '-y' ,'-i', str(self._abs_in_path) , '-crf', str(crf), '-filter:v' ,f'fps=fps={fps}' , str(self._abs_out_path)]
        try:
            process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
            _, err = process.communicate()
            return True
        except Exception as ex:
            logger.info(ex.args)
            return False

class VideoUploader():
    def __init__(self, received_file, abs_out_path):
        self._received_file = received_file
        self._abs_out_path = abs_out_path
    def saveFile(self):
        try:
            self._received_file.save(self._abs_out_path)
            return True
        except Exception as exc:
            logger.info(exc.args)
            return False

    def update_cookies(self, session_key, data):
        if(session.get(session_key) is None):
            session[session_key] = data
        else:
            temp = session.get(session_key)
            temp.append(data)
            session[session_key] = temp


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
                file_path = os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, unique_path)) + ext
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