import os
import logging
import errno
import random
import uuid
import datetime
import subprocess as sp
import urllib
from config import UPLOAD_FOLDER, RESULT_FOLDER, REDIS_URL, SECRET_KEY
from time import sleep
from flask import Flask, request, abort, jsonify, session
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
    session["filename"] = list()

@celery.task()
def video_converter(unique_path, ext, crf, fps):
    filename, _ = os.path.splitext(unique_path)
    logger.info(f'{filename}')
    print(str(unique_path))
    filename = filename.split('/')[1]
    s_filename = secure_filename(filename)
    logger.info(f'{s_filename}')
    in_path = os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, unique_path))
    unique_filename = f'{s_filename}{ext}'
    #command = f'ffmpeg -i {in_path} -crf={crf} -filter:v fps={fps} {unique_filename}'
    out_path = os.path.abspath(os.path.join(os.getcwd(), RESULT_FOLDER, unique_filename))
    command = ['ffmpeg', '-y' ,'-i', str(in_path), '-crf', str(crf), '-filter:v' ,f'fps=fps={fps}' , str(out_path)] 
    process = sp.Popen(command)
    process.communicate()
    return out_path

@celery.task(name='file-saving-task')
def save_file(file):
    path = os.path.abspath(os.path.join(os.getcwd, UPLOAD_FOLDER, filename))

@app.route('/video_converter', methods=['POST'])
def get_convert():
    if request.method == 'POST':
        unique_path = request.args.get('unique_path')
        ext = request.args.get('ext')
        crf = request.args.get('crf')
        fps = request.args.get('fps')
        print(unique_path, ext, crf, fps)
        task = video_converter.delay(unique_path, ext, crf, fps)
        async_result = AsyncResult(id=task.task_id, app=celery)
        url = async_result.get()
        return url

@app.route('/get', methods=['POST'])
def get_cache():
    if request.method == 'POST':
        a = session.get("filename")
        return jsonify(cachess = a)

@app.route('/upload', methods=['POST'])
def upload():
    """Upload file endpoint."""
    if request.method == 'POST':
        if not request.files.get('file', None):
            msg = 'the request contains no file'
            logger.error(msg)

        received_file = request.files['file']
        if received_file:  #tambahkan validasi
            msg = f'the file {received_file.filename} has wrong extention'
            logger.error(msg)
        dirname_by_day = str(datetime.date.today())
        if(os.path.isdir(os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, dirname_by_day))) is not True):
            try:
                os.mkdir(os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, dirname_by_day)))
            except OSError as exc:
                print(exc.args)
        s_filename = secure_filename(received_file.filename)
        s_filename, file_extension = os.path.splitext(s_filename)
        unique_filename = f'{dirname_by_day}_{uuid.uuid4()}_{s_filename}{file_extension}'
        saving_path = os.path.abspath(os.path.join(os.getcwd(), UPLOAD_FOLDER, dirname_by_day, unique_filename))
        unique_path = os.path.join(dirname_by_day, unique_filename)
        try:
            received_file.save(saving_path)
            temp = session.get("filename")
            temp.append(unique_path)
            session["filename"] = temp
            print(str(session["filename"]))
        except Exception as exc:
            print(exc.args)
            pass
        logger.info(f'the file {received_file.filename} has been successfully saved as {unique_filename}')
        return s_filename