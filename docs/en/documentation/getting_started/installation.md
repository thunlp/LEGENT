# Installation

LEGENT supports Windows/Linux/MacOS/Web.

## Install Platform Toolkit

It is recommended to use Conda to manage the environment:

```
conda create -n legent python=3.10
conda activate legent
```

Install the toolkit:
``` bash
git clone https://github.com/thunlp/LEGENT
cd LEGENT
pip install -e .
```

If your network cannot access GitHub, use ssh to clone the repository:

``` bash
git clone git@ssh.github.com:thunlp/LEGENT.git
```

## Download Environment Client

### download automaticlly (recommended)

After installing the toolkit, run the following command:

``` bash
legent download
```

If your network cannot access Huggingface Hub, run:

``` bash
legent download --thu
```

It will automatically download the latest version of the client for your system to the `.legent/env` folder in the current directory.


### download manually (not recommended)

If auto-download fails, you can manually download the client. Download from [Huggingface Hub](https://huggingface.co/LEGENT/LEGENT-environment-Alpha/tree/main) or [Tsinghua Cloud](https://cloud.tsinghua.edu.cn/d/9976c807e6e04e069377/). After downloading, extract the file to create the following file structure:

```
LEGENT/
└── .legent/
    └── env/
        ├── client
        │   └── LEGENT-<platform>-<version>
        └── env_data/
            └── env_data-<version>
```

For Linux or MacOS users, you need to modify file permissions:

```
chmod -R 777 .legent/env
```

## Run On Linux Server (Optional)

Normally, we train and deploy models on Linux servers, which often do not have a display. We recommend the following methods: 

1. Use the remote communication function of LEGENT. Use the environment on your local computer and train the model on the server.
   
    We recommend using this method first, as it is very convenient for visually using and debugging.

2. Use Xvfb.

    If you do not wish to be bottlenecked by network performance, such as when needing large-scale parallel sampling, you need to use Xvfb on the Linux servers to support rendering.

    If you have root access to the server, you can install Xvfb by using:
    ```
    sudo apt install xvfb
    ```
    
    Prepend `xvfb-run` to commands that run Python scripts. For example:
    ```
    xvfb-run python demo.py
    ```

3. Use Docker.
   
    Not ready.