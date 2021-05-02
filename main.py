import subprocess, sys
from flask_bootstrap import Bootstrap
import os, zipfile, configparser, shutil
from distutils.dir_util import copy_tree
from werkzeug.utils import secure_filename
from flask import Flask, request, redirect
from flask import url_for, flash, render_template

ALLOWED_EXTENSIONS = set(['zip'])
PROJECTS_FOLDER = os.path.join(os.getcwd(), 'server', 'apps')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'server', 'updates')

app = Flask(__name__)
Bootstrap(app)
app.secret_key = '03dsf24gd87dj756'


def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def getconfigs(project):
  config = configparser.RawConfigParser()
  config.read(f'{UPLOAD_FOLDER}/{project}/config.cfg')
  proj_config = dict(config.items("SERVER_CONFIG"))
  return (proj_config.get('root'), proj_config.get('project'))


def stopProject(project, path):
  if sys.platform.lower() == 'linux':
    os.system(f"pkill -f \'python {path}\'")
  else:
    found = subprocess.check_output(f"tasklist /FI \"windowtitle eq {project} project\"", shell=True)
    if not found.decode("utf-8").startswith('INFO: No tasks'):
      subprocess.check_output(f"taskkill /F /FI \"WINDOWTITLE eq  {project} project\"", shell=True)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    if 'file' not in request.files:
      flash('No file part')
      return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
      flash('No selected file')
      return redirect(request.url)
    if file and allowed_file(file.filename):
      # ====================== create and extract zip =================
      filename = secure_filename(file.filename)
      file.save(os.path.join(UPLOAD_FOLDER, filename))
      zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r')
      zip_ref.extractall(UPLOAD_FOLDER)
      zip_ref.close()
      # =================== delete the zip from updates ======================
      os.remove(os.path.join(UPLOAD_FOLDER, filename))
      newfolder = filename.replace('.zip', '')
      root, project = getconfigs(newfolder)
      # ============== stop the original app and update files =================
      project_path = os.path.join(PROJECTS_FOLDER, project, f'{root}.py')
      stopProject(project, project_path)
      copy_tree(f"{UPLOAD_FOLDER}/{newfolder}", f"{PROJECTS_FOLDER}/{project}")
      # ====================== delete the folder from updates =================
      if os.path.isdir(f"{UPLOAD_FOLDER}/{newfolder}"):
        shutil.rmtree(f"{UPLOAD_FOLDER}/{newfolder}")
      # ===================== restart the project and notify user =============
      if sys.platform.lower() == 'linux':
        os.system(f"xterm -e \'python {project_path}\' &")
      else:
        subprocess.Popen(["cmd", "/c", "START", f"{project} project", "python", project_path])
      return redirect(url_for('upload_file'))
  return render_template('index.html')


if __name__ == "__main__":
  app.run(host='0.0.0.0', port='5000')