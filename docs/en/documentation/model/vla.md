# Vision-Language-Action


Large language models (LLM) are trained on massive amounts of text. LLMs contain certain world knowledge and exhibit sparks of general intelligence. However, they lack capabilities in embodied perception and control. Vision language models (VLM) typically start with LLMs and incorporate image-text data for training, enabling them to perceive images.

A practical step towards obtaining a rudimentary general-purpose embodied model is to start with a VLM and train it with embodied data, such as robot trajectories. This process equips the model with the capability for embodied perception and control within physical environments. The further trained VLMs are known as vision-language-action (VLA) models. VLAs have the potential to obtain a range of emergent capabilities. Read the paper *[RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control](https://arxiv.org/abs/2307.15818)* to learn more.

The availability of open-source VLA models is currently limited. LEGENT has created embryonic VLA models leveraging open-source foundational models and generated data. Large-scale training with more tasks and trajectories is in progress.

We demonstrated how to train with [single-image](/documentation/model/single_image/) or [multi-image](/documentation/model/multi_image/) models.
