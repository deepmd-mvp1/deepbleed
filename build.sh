docker build --no-cache -t anilyerramasu/deepbleed .
docker run  --gpus all --ipc=host --rm -p 9000:5000 -v $(pwd)/input:/home/input -v $(pwd)/output:/home/output anilyerramasu/deepbleed 

python3 predict.py --verbose --indir /home/input --outdir /home/output --weights weights