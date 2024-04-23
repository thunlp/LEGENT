# Installation

LEGENT supports Windows/Linux/MacOS/Web.

## Install Platform Toolkit

``` bash
git clone https://github.com/thunlp/LEGENT
cd LEGENT
pip install -e .
```

or using ssh:

``` bash
git clone git@ssh.github.com:thunlp/LEGENT.git
```

## Download Environment Client

### download automaticlly (recommended)

After installing the toolkit, run the following command:

```
legent download
```

It will automatically download the latest version of the client for your system to the `.legent/client` folder in the current directory.


### download manually

If auto-download fails, you can manually download the client. Download from Googole Drive (not ready) or [Tsinghua Cloud](https://cloud.tsinghua.edu.cn/d/9976c807e6e04e069377/) and extract the file.
For Linux or MacOS users, you need to modify file permissions.

For example:
```
unzip LEGENT-linux-<version>.zip
chmod -R 777 LEGENT-linux/*
```

## Run On Linux Server (Optional)

Normally, we train and deploy models on Linux servers, which often do not have a display. We recommend the following methods: 

1. Use the remote communication feature of LEGENT. Use the environment on your local computer and train the model on the server.

2. Use Xvfb.

    We recommend the first method, as it is very convenient for visually using and debugging. If you do not wish to be bottlenecked by network performance, such as when needing large-scale parallel sampling, you need to use Xvfb on the Linux servers to support rendering.
    
    If you have root access to the server, you can install Xvfb by using:
    ```
    sudo apt install xvfb
    ```
    
    Prepend `xvfb-run` to commands running Python scripts. For example:
    ```
    xvfb-run python demo.py
    ```

3. Use Docker.
   
    Not ready.