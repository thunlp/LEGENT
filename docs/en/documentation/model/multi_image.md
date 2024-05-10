# Multi-Image VLA

We use [VILA](https://github.com/Efficient-Large-Model/VILA) for training a VLA model with multi-image input.

!!! warning "Note"
    The models for multi-image or video input are still in its early stages, the platform is urgently experimenting. Currently, VILA can only handle a maximum of six images. We use a window of six images to input the observations.

## Training

Clone repository:

``` bash
git clone https://github.com/Efficient-Large-Model/VILA
cd VILA
```

Install VILA:

??? abstract "[Install VILA](https://github.com/Efficient-Large-Model/VILA?tab=readme-ov-file#installation)"
    ``` bash
    conda create -n vila python=3.10 -y
    conda activate vila

    pip install --upgrade pip  # enable PEP 660 support
    wget https://github.com/Dao-AILab/flash-attention/releases/download/v2.4.2/flash_attn-2.4.2+cu118torch2.    0cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
    pip install flash_attn-2.4.2+cu118torch2.0cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
    pip install -e .
    pip install -e ".[train]"

    pip install git+https://github.com/huggingface/transformers@v4.36.2
    cp -rv ./llava/train/transformers_replace/* ~/anaconda3/envs/vila/lib/python3.10/site-packages/transformers/    models/
    ```



Generate the training data we need. 

??? abstract "Data Generation"
    On the remote server, run:

    ``` bash
    xvfb-run python scripts/create_traj_come.py
    ```

    or 

    ``` bash
    xvfb-run python scripts/create_traj_where.py
    ```

    The dataset will be saved at `.legent/dataset` on the remote server.

To Edit
