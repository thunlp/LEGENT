

各个文件说明：

- ann_main.py：

  - 用于标注单个物体的各个属性。
  - 输入为含有待标注物体名称的json文件。如data_requirements.json
  - 输出为各个物体的各个属性值的xlsx表格

- ann_rec.py

  - 用于判断该物体是否为receptacle
  - 输入为含有待标注物体名称得json文件。如data_requirements.json
  - 输出为各个物体关于是否为receptacle的xlsx表格

- ann_relation.py

  - 用于标注receptacles和非receptacle的物体之间的共现关系
  - 输入为ann_rec.py输出的关于一个物体是否为receptacle的xlsx表格
  - 输出为关于共现关系的json文件

- ann_script.py

  - 用于将上述三个代码合在一起的自动化执行脚本

    例如：

    `python  .\ann_script.py --unlabeled_objects test_require.json --object_annotations obj.xlsx --receptacles rec.xlsx --relations rel.json`

