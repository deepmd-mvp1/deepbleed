FROM nvcr.io/nvidia/tensorflow:22.11-tf2-py3
# FROM nvcr.io/nvidia/pytorch:20.10-py3
#install useful packages

RUN mkdir /home/deepbleed

WORKDIR /home/deepbleed
RUN mkdir /home/deepbleed/templates
RUN mkdir /home/deepbleed/blocks
RUN mkdir /home/deepbleed/models
RUN mkdir /home/deepbleed/preprocess
RUN mkdir /home/deepbleed/tools
COPY * /home/deepbleed/
COPY templates/ /home/deepbleed/templates/
COPY blocks/ /home/deepbleed/blocks/
COPY models/ /home/deepbleed/models/
COPY preprocess/ /home/deepbleed/preprocess/
COPY tools/ /home/deepbleed/tools/

RUN pip  install tensorflow \
    Pillow \
    h5py \
    keras_preprocessing \
    matplotlib \
    mock \
    numpy \
    scipy \
    sklearn \
    pandas \
    future \
    portpicker \
    enum34 \
    #imaging packages
    nibabel \
    six \
    scikit-image \
    webcolors \
    plotly \
    webcolors \
    fslpy \
    flask \
    flask_cors


RUN pip install antspyx
#https://github.com/ANTsX/ANTsPy/releases/download/v0.2.0/antspyx-0.2.0-cp37-cp37m-linux_x86_64.whl


#Install FSL base, but not unneeded extras
ENV INSTALL_FOLDER=/usr/local/

RUN curl -sSL https://fsl.fmrib.ox.ac.uk/fsldownloads/fsl-6.0.2-centos7_64.tar.gz | tar xz -C ${INSTALL_FOLDER} \
    --exclude='fsl/doc' \
    --exclude='fsl/data/first' \    
    --exclude='fsl/data/atlases' \
    --exclude='fsl/data/possum' \    
    --exclude='fsl/src' \    
    --exclude='fsl/extras/src' \    
    --exclude='fsl/bin/fslview*' \
    --exclude='fsl/bin/FSLeyes' \
    --exclude='fsl/bin/*_gpu*' \
    --exclude='fsl/bin/*_cuda*'

# Configure environment
ENV FSLDIR=${INSTALL_FOLDER}/fsl/ \
    FSLOUTPUTTYPE=NIFTI_GZ

# Below needs a new line
ENV PATH=${FSLDIR}/bin:$PATH \
    LD_LIBRARY_PATH=${FSLDIR}:${LD_LIBRARY_PATH}

RUN mkdir /.local && chmod a+rwx /.local
RUN cd /home
# RUN git clone https://github.com/deepmd-mvp1/deepbleed.git

# download the weights
RUN wget -O weights.zip https://www.dropbox.com/s/v2ptd9mfpo13gcb/mistie_2-20200122T175000Z-001.zip?dl=1  && unzip -j weights.zip 
RUN for i in _data-00001-of-00002 _data-00000-of-00002 _index; do out=`echo ${i} | sed "s/_/weights./"`; mv ${i} ${out}; done
RUN pwd
RUN ls -al
ENV FLASK_APP=App.py
# RUN  /home/pipeline.sh 
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]