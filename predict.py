# @author: msharrock
# version: 0.0.1


"""
Prediction Script for DeepBleed

Command Line Arguments:
        --indir: string, location to perform prediction
        --outdir: string, location to save predictions
        --weights: string, location of model weights
        --cpus: int, optional, number of cpu cores to utilize
        --gpus: int, optional, number of gpus to utilize
        --verbose: optional, script is verbose and timed
        --brain: optional, image is brain-only, extraction skipped
"""

import os
import fsl
import ants
import time
import nibabel as nib
import tensorflow as tf

from tools import parse
from preprocess import extract, register, convert
from models.vnet import VNet

# load command line arguments
setup = parse.args('predict')
verbose = setup.verbose
brain_only = setup.brain

# environmental variable setup
os.environ["ANTS_RANDOM_SEED"] = '1'
os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'

if setup.CPUS:
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(setup.CPUS)

if setup.GPUS:
    os.environ['CUDA_VISIBLE_DEVICES'] = ','.join(map(str,range(setup.GPUS)))
else:
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'

# set paths to scripts, templates, weights etc.
TEMPLATE_PATH = os.path.join('templates', 'scct_unsmooth_SS_0.01_128x128x128.nii.gz')

if setup.weights:
    WEIGHT_PATH = setup.weights
else:
    WEIGHT_PATH = 'weights'

# load the model and weights
model = VNet()
model.load_weights(WEIGHT_PATH)

# setup directory trees
IN_DIR = setup.IN_DIR
OUT_DIR = setup.OUT_DIR
if not os.path.exists(IN_DIR):
    os.mkdir(IN_DIR)
if not os.path.exists(OUT_DIR):
    os.mkdir(OUT_DIR)

# load input data
files = sorted(next(os.walk(IN_DIR))[2])
files = [os.path.join(IN_DIR, f) for f in files]
template = ants.image_read(TEMPLATE_PATH, pixeltype = 'float')

for filename in files:

    # preprocessing
    if verbose:
        timestamp = time.time()
        print('loading:', filename)
    original_image = nib.load(filename)
    original_header = original_image.header
    original_affine = original_image.affine
    original_image = convert.nii2ants(original_image)


    if brain_only:
        image = original_image
    else:
        image = nib.load(filename)
        #nib.save(image, "loaded.nii.gz")
        if verbose:
            print('brain extraction')
        image = extract.brain(image)
        nib.save(image, "predict_extracted.nii.gz")
        image = convert.nii2ants(image)
    print(image)

    if verbose:
        print('template registration')
    image, transforms = register.rigid(template, image)
#    print("====")
#    print(image)
#    print(transforms)
#    print(len(transforms))
#    print("===")
    image, ants_params = convert.ants2np(image)


    # neural net prediction
    if verbose:
        print('generating prediction')
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

    # invert registration
    if verbose:
        print('inverting registration')
    prediction = register.invert(original_image, prediction, transforms)
    prediction = nib.Nifti1Image(prediction.numpy(), header=original_header, affine=original_affine)

    if verbose:
        print('saving:', os.path.join(OUT_DIR, os.path.basename(filename)))
    nib.save(prediction, os.path.join(OUT_DIR, os.path.basename(filename).split(".")[0] +  "_prediction.nii.gz"))

    if verbose:
        print(os.path.basename(filename), ': took {0} seconds !'.format(time.time() - timestamp))
if verbose:
   	print ('All files complete, the pipeline took {0} seconds !'.format(time.time() - timestamp))
