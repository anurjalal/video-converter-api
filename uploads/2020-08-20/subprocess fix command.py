import subprocess as sp
import csv
import re

ext = "avdi"
command = ['ffmpeg', '-h' ,f'muxer={ext}']
a = sp.run(command, stdout=sp.PIPE)
x = re.search("Unknown format+", str(a.stdout))
if x:
  print("YES! We have a match!")
else:
  print("No match")

