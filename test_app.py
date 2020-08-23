import os
import unittest
from datetime import datetime
from app import app
import io
import json

class VideoConverterApi(unittest.TestCase):
    """This class represents the agency test case"""

    testdir = 'testvid'
    unique_path = ""
    session_upload_key = "upload_filename"
    def setUp(self):
        """Define test variables and initialize app."""

        self.app = app
        self.client = self.app.test_client
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    def test_upload(self):
        data = {}
        data['file'] = (io.BytesIO(b''), 'testvid/test.mp4')
        response = self.client().post('/upload',
            data=data, follow_redirects=True,
            content_type='multipart/form-data'
        )
        self.assertEqual(200, response.status_code)

    def test_error_400_upload(self):
        data = {}
        data['files'] = (io.BytesIO(b''), 'testvid/test.exe')
        response = self.client().post('/upload',
            data=data, follow_redirects=True,
            content_type='multipart/form-data'
        )
        self.assertEqual(400, response.status_code)
    
    def test_convert(self):
        unique_path = "23-08-2020/test.mp4"
        ext = ".avi"
        crf = "20"
        fps = "20"
        data = {
            "unique_path" : unique_path,
            "ext" : ext,
            "crf" : crf,
            "fps" : fps
        }
        response = self.client().get('/converter',query_string= data)
        self.assertEqual(200, response.status_code)
    
    def test_error_400_convert(self):
        unique_path = "23-08-2020/test.mp4"
        ext = ".vi"
        crf = "a0"
        fps = "klmn"
        data = {
            "unique_path" : unique_path,
            "ext" : ext,
            "crf" : crf,
            "fps" : fps
        }
        response = self.client().get('/converter',query_string= data)
        self.assertEqual(400, response.status_code)

if __name__ == "__main__":
    unittest.main()