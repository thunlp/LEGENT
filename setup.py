from setuptools import setup, find_packages


def get_requirements():
    with open('requirements.txt', 'r') as f:
        ret = [line.strip() for line in f.readlines()]
        print("requirements:", ret)
    return ret


setup(
    name='legent',
    version='0.0.0',
    description='',
    author='THUNLP',
    url='https://github.com/thunlp/LEGENT-dev',
    author_email='chengzl22@mails.tsinghua.edu.cn',
    download_url='https://github.com/chengzl18/LEGENT-dev/archive/master.zip',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords=['nlp', 'embodied', 'ai'],
    python_requires=">=3.6.0",
    install_requires=[
        "pyqtree", "flask", "huggingface_hub", "colorama", "cloudpickle", "grpcio==1.59.2", "numpy>=1.14.1", "Pillow>=4.2.1", "protobuf==3.20.3", "pyyaml>=3.1.0", "filelock>=3.4.0", "scikit-image", "tqdm", "openai==1.10.0",
        "paramiko", "sshtunnel",
        "shapely==2.0.3", "attrs==23.2.0", "pandas==2.2.1", "matplotlib==3.8.3"
    ],
    extras_require={
        "llava": [
            "torch==2.0.1", "torchvision==0.15.2",
            "transformers==4.31.0", "tokenizers>=0.12.1,<0.14", "sentencepiece==0.1.99", "shortuuid",
            "accelerate==0.21.0", "peft==0.4.0", "bitsandbytes==0.41.0",
            "pydantic<2,>=1", "markdown2[all]", "numpy", "scikit-learn==1.2.2",
            "gradio==3.35.2", "gradio_client==0.2.9",
            "requests", "httpx==0.24.0", "uvicorn", "fastapi",
            "einops==0.6.1", "einops-exts==0.0.4", "timm==0.6.13",
        ] + ["deepspeed==0.9.5", "ninja", "wandb"],
    },

    packages=find_packages(),
    package_data={'': ['*.json']},
    entry_points={
        "console_scripts": [
            "legent=legent:main",
        ]
    }
)
