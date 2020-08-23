from flask import session

class VideoUploader():
    
    def __init__(self, received_file, abs_out_path):
        self._received_file = received_file
        self._abs_out_path = abs_out_path

    def saveFile(self):
        try:
            self._received_file.save(self._abs_out_path)
            return True
        except Exception as exc:
            print(exc.args)
            return False

    def update_cookies(self, session_key, data):
        if(session.get(session_key) is None):
            session[session_key] = data
        else:
            temp = session.get(session_key)
            temp.append(data)
            session[session_key] = temp
