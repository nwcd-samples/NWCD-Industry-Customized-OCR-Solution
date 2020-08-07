# ocr-craft-cn-pytorch

中文 文本区域检测和文本识别的pytorch实现


# 文本识别 Demo 测试

修改对应参数  输入输出文件夹路径 以及两个模型的路径 
```
python3 ocr_main.py  \
-i 'temp/input/' \                                   #修改
-o 'temp/output/' \                                  #修改
--cuda==False  \
--batch_size 32 \
--label_file_list  'sample_data/chars.txt' \            
--Transformation TPS \
--FeatureExtraction ResNet \
--SequenceModeling BiLSTM \
--Prediction Attn \
--saved_model atte/saved_models/TPS-ResNet-BiLSTM-Attn-Seed1111/best_accuracy.pth \   #修改
--trained_model  'craft/weights/craft_mlt_25k.pth'                                    #修改  
```


# CRAFT 文本区域检测

Official Pytorch implementation of CRAFT text detector | [Paper](https://arxiv.org/abs/1904.01941) | [Pretrained Model](https://drive.google.com/open?id=1Jk4eGD7crsqCCg9C9VjCLkMN3ze8kutZ) | [Supplementary](https://youtu.be/HI8MzpY8KMI)


[Github参考代码](https://github.com/clovaai/CRAFT-pytorch)

### Test instruction using pretrained model
- Download the trained models
 
 *Model name* | *Used datasets* | *Languages* | *Purpose* | *Model Link* |
 | :--- | :--- | :--- | :--- | :--- |
General | SynthText, IC13, IC17 | Eng + MLT | For general purpose | [Click](https://drive.google.com/open?id=1Jk4eGD7crsqCCg9C9VjCLkMN3ze8kutZ)
IC15 | SynthText, IC15 | Eng | For IC15 only | [Click](https://drive.google.com/open?id=1i2R7UIUqmkUtF0jv_3MXTqmQ_9wuAnLf)
LinkRefiner | CTW1500 | - | Used with the General Model | [Click](https://drive.google.com/open?id=1XSaFwBkOaFOdtk4Ane3DFyJGPRw6v5bO)

* Run with pretrained model
``` (with python 3.7)
python test.py --trained_model=[weightfile] --test_folder=[folder path to test images]

```



#  文本识别
| [paper](https://arxiv.org/abs/1904.01906) | [training and evaluation data](https://github.com/clovaai/deep-text-recognition-benchmark#download-lmdb-dataset-for-traininig-and-evaluation-from-here) | [failure cases and cleansed label](https://github.com/clovaai/deep-text-recognition-benchmark#download-failure-cases-and-cleansed-label-from-here) | [pretrained model](https://drive.google.com/drive/folders/15WPsuPJDCzhp2SvYZLRj8mAlT3zmoAMW) | [Baidu ver(passwd:rryk)](https://pan.baidu.com/s/1KSNLv4EY3zFWHpBYlpFCBQ) |


[Github参考代码](https://github.com/clovaai/deep-text-recognition-benchmark)



### 生成文本识别的数据

```
cd data_generate

sh generation.sh 'demo.txt'  0.2   ../output/

```


### 进行文本识别训练

```
cd atte
sh run.sh

```





### 中文文档文字识别 数据简介


共约364万张图片，按照99:1划分成训练集和验证集。
数据利用中文语料库（新闻 + 文言文），通过字体、大小、灰度、模糊、透视、拉伸等变化随机生成
包含汉字、英文字母、数字和标点共5990个字符（字符集合：https://github.com/YCG09/chinese_ocr/blob/master/train/char_std_5990.txt ）
每个样本固定10个字符，字符随机截取自语料库中的句子
图片分辨率统一为280x32


下载地址：[https://pan.baidu.com/s/1QkI7kjah8SPHwOQ40rS1Pw  ](https://pan.baidu.com/s/1QkI7kjah8SPHwOQ40rS1Pw)   (密码： `lu7m`  )

