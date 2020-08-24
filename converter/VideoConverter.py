import subprocess as sp


class VideoConverter:

    def __init__(self, abs_in_path, abs_out_path):
        self._abs_in_path = abs_in_path
        self._abs_out_path = abs_out_path

    def convert(self, crf, fps):
        command = ['ffmpeg', '-y', '-i', str(self._abs_in_path), '-crf', str(crf), '-filter:v', f'fps=fps={fps}',
                   str(self._abs_out_path)]
        try:
            process = sp.Popen(command, stdout=sp.PIPE, stderr=sp.PIPE)
            _, err = process.communicate()
            return True
        except Exception as exc:
            print(exc.args)
            return False
