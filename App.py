
import os
import fsl
import ants
import time
import nibabel as nib
import tensorflow as tf

from tools import parse
from preprocess import extract, register, convert
from models.vnet import VNet
from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
import subprocess
import json
import tempfile
from flask import jsonify, send_file
from flask_cors import CORS


app=Flask(__name__)
CORS(app)

app.secret_key = "secret key"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024 * 1024

# Get current path
path = os.getcwd()
# file Upload
UPLOAD_FOLDER = "/home/input"

os.environ["ANTS_RANDOM_SEED"] = '1'
os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
WEIGHT_PATH = 'weights'
# set paths to scripts, templates, weights etc.
TEMPLATE_PATH = os.path.join('template', 'scct_unsmooth_SS_0.01_128x128x128.nii.gz')

# load the model and weights
model = VNet()
model.load_weights(WEIGHT_PATH)

# setup directory trees
IN_DIR = "/home/input"
OUT_DIR = "/home/output"
if not os.path.exists(IN_DIR):
    os.mkdir(IN_DIR)
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

template = ants.image_read(TEMPLATE_PATH, pixeltype = 'float')

@app.route('/bleed/predict', methods=['GET'])
def upload_form():
    return render_template('upload.html')
# load input data
@app.route('/bleed/predict', methods=['POST'])
def upload():
    print("inside ---")
    # os.mkdir(app.config['UPLOAD_FOLDER'])
    if request.method == 'POST':

        
        print("inside ---")
        files = request.files.getlist('files[]')
        IN_DIR = tempfile.mkdtemp(dir="/home/input")
       
        OUT_DIR = tempfile.mkdtemp(dir="/home/output")
        

        for file in files:
            filename = secure_filename(file.filename)
            print(filename)
            file.save(inputDir +"/" +filename)
            original_image = nib.load(filename)
            original_header = original_image.header
            original_affine = original_image.affine
            original_image = convert.nii2ants(original_image)
            image = nib.load(filename)
            image = extract.brain(image)
            nib.save(image, "predict_extracted.nii.gz")
            image = convert.nii2ants(image)
            image, transforms = register.rigid(template, image)
            image, ants_params = convert.ants2np(image)
            prediction = model.predict(image)
            prediction = convert.np2ants(prediction, ants_params)
    # warp to MNI
            mni_transform = "ct2mni.mat"
            mni_template = nib.load("icbm152_t1_tal_nlin_asym_09c_masked.nii.gz")
            mni_affine = mni_template.affine
            mni_header = mni_template.header
            mni_img = ants.apply_transforms(convert.nii2ants(mni_template), prediction, [mni_transform])
            mni_img = nib.Nifti1Image(mni_img.numpy(), header=mni_header, affine=mni_affine)
            nib.save(mni_img, os.path.join(OUT_DIR, os.path.basename(filename).split(".")[0] +  "_mni_prediction.nii.gz"))
            prediction = register.invert(original_image, prediction, transforms)
            prediction = nib.Nifti1Image(prediction.numpy(), header=original_header, affine=original_affine)
            nib.save(prediction, os.path.join(OUT_DIR, os.path.basename(filename).split(".")[0] +  "_prediction.nii.gz"))
            sendfile = os.path.join(OUT_DIR, os.path.basename(filename).split(".")[0] +  "_mni_prediction.nii.gz")
            return send_file(sendfile, mimetype="application/zip, application/octet-stream, application/x-zip-compressed, multipart/x-zip")





    
    
    return 

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=False,threaded=True)

