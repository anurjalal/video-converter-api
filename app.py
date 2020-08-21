import os
import logging
import errno
import random
import uuid
import datetime
import subprocess as sp
import urllib
import re
from config import UPLOAD_FOLDER, RESULT_FOLDER, REDIS_URL, SECRET_KEY
from time import sleep
from flask import Flask, request, abort, jsonify, session, send_from_directory, Response
from collections import Counter
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
    session["upload_filename"] = list()

@app.route('/upload', methods=['POST'])
def upload():
    """Upload file endpoint."""
    if request.method == 'POST':
        if not request.files.get('file', None):
            err_mssg = "A file is required!"
            return abort(Response(err_mssg, 400))
        received_file = request.files['file']
        filename, ext = os.path.splitext(received_file.filename)
        # check video format
        if(not is_vid_format_valid(ext)):
            err_mssg = f'video format of {filename} is not accepted.'
            return abort(Response(err_mssg, 400))
        dirname_by_day = str(datetime.date.today())
        if(os.path.isdir(os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, dirname_by_day))) is not True):
            try:
                os.mkdir(os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, dirname_by_day)))
            except OSError as exc:
                logger.info(exc.args)
        s_filename = secure_filename(received_file.filename)
        s_filename, ext = os.path.splitext(s_filename)
        unique_filename = f'{dirname_by_day}_{uuid.uuid4()}_{s_filename}{ext}'
        saving_path = os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, dirname_by_day, unique_filename))
        unique_path = os.path.join(dirname_by_day, unique_filename)
        try:
            received_file.save(saving_path)
            temp = session.get("upload_filename")
            temp.append(unique_path)
            session["upload_filename"] = temp
            return jsonify({
            'succes': True,
            'message': f'the file {received_file.filename} has been successfully uploaded'
        })
        except Exception as exc:
            logger.info(exc.args)
        err_mssg = f'the file {received_file.filename} failed to upload'
        abort(Response(err_mssg, 400))

@celery.task()
def video_converter(unique_path, ext, crf, fps):
    filename, _ = os.path.splitext(unique_path)
    print(str(unique_path))
    filename = filename.split('/')[1]
    s_filename = secure_filename(filename)
    in_path = os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, unique_path))
    unique_filename = f'{s_filename}{ext}'
    out_path = os.path.abspath(os.path.join(os.getcwd(), RESULT_FOLDER, unique_filename))
    command = ['ffmpeg', '-y' ,'-i', str(in_path), '-crf', str(crf), '-filter:v' ,f'fps=fps={fps}' , str(out_path)]
    try:
        process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
        _, err = process.communicate()
    except Exception as ex:
        logging.info(ex.args)
    return out_path

@app.route('/video_converter', methods=['GET'])
def get_convert():
    if request.method == 'GET':
        unique_path = request.args.get('unique_path')
        ext = request.args.get('ext')
        crf = request.args.get('crf')
        fps = request.args.get('fps')
        print(unique_path, ext, crf, fps)
        task = video_converter.delay(unique_path, ext, crf, fps)
        async_result = AsyncResult(id=task.task_id, app=celery)
        out_path = async_result.get()
        return send_from_directory(os.path.dirname(out_path), os.path.basename(out_path))

def is_vid_format_valid(ext):
    ext_without_dot = ext.replace('.', '')
    cmd = ['ffmpeg', '-h' ,f'muxer={ext_without_dot}']
    process = sp.run(cmd, stdout=sp.PIPE)
    inv_messg = re.search("Unknown format+", str(process.stdout))
    if inv_messg:
        return False
    else:
        return True