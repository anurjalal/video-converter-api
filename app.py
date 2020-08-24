import sys
sys.path.insert(1, 'converter/')
sys.path.insert(1, 'helper/')
sys.path.insert(1, 'config/')
import os
import logging
from datetime import datetime
from config import UPLOAD_FOLDER, RESULT_FOLDER, SECRET_KEY
from flask import Flask, request, jsonify, session, send_from_directory, Response
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from celery import Celery, Task
from celery_config import make_celery
from FileHelper import FileHelper
from PathHelper import PathHelper
from Validation import Validation
from VideoConverter import VideoConverter
from VideoHelper import VideoHelper
from VideoUploader import VideoUploader


app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://redis:6379/0',
    CELERY_RESULT_BACKEND='redis://redis:6379/0'
)
celery = make_celery(app)
logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)
app.secret_key = SECRET_KEY

@app.before_first_request
def before_first_request_func():
    session["upload_filename"] = []

@app.route('/upload', methods=['POST'])
def upload():
    """Upload file endpoint."""
    if request.method == 'POST':
        if not request.files.get('file', None):
            msg = "invalid request. "
            return jsonify({
                'success' : False,
                'message' : msg
                }), 400
        received_file = request.files['file']
        _, ext = os.path.splitext(received_file.filename)
        file_helper = FileHelper(received_file.filename)
        video_helper = VideoHelper(file_helper)
        ext_without_dot = file_helper.get_ext_without_dot()
        upload_validator = Validation()
        if(not upload_validator.is_vid_format_valid(ext_without_dot)):
            msg = f'video format of {received_file.filename} is not accepted.'
            return jsonify({
                'success' : False,
                'message' : msg
                }), 400
        daily_folder = video_helper.generateDailyFolder(UPLOAD_FOLDER)
        out_path = video_helper.generateUploadPathname(daily_folder)
        uploader = VideoUploader(received_file, out_path)
        if(uploader.saveFile()):
            data = os.path.join(PathHelper(out_path).get_simple_directory(), os.path.basename(out_path))
            session_key = "upload_filename"
            uploader.update_cookies(session_key, data)
            return jsonify({
            'success': True,
            'message': f'the file {received_file.filename} has been successfully uploaded',
            'data' : data
            })
        msg = f'File failed to upload'
        return jsonify({
                'success' : False,
                'message' : msg
                }), 400

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
           return jsonify({
                'success' : False,
                'message' : msg_validation
                }), 400
        task = video_converter.delay(unique_path, ext, crf, fps)
        async_result = AsyncResult(id=task.task_id, app=celery)
        err, msg = async_result.get()
        if(err != 0):
            return jsonify({
                'success' : False,
                'message' : msg
                }), 400
        else:
            return send_from_directory(os.path.dirname(msg), os.path.basename(msg))

@app.route('/upload_path', methods=['GET'])
def get():
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': session.get("upload_filename")
            }),200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug = True)