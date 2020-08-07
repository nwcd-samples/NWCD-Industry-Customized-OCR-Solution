# This is the file that implements a flask server to do inferences. It's the file that you will modify to
# implement the scoring for your own algorithm.

from __future__ import print_function

import os
import cv2
import sys
import time
import uuid
import json
import glob
import boto3
import flask
import errno
import shutil
import datetime
from PIL import Image
from pathlib import Path
from multiprocessing import Pool
from collections import OrderedDict


import traceback
import json
import shutil
import numpy as np
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
from torch.autograd import Variable
from craft.craft import CRAFT
from craft.text_detection import text_detection_single 
from craft.text_detection import copyStateDict
from craft.merge_box import do_merge_box
from recognition.recognition import test_recong
from recognition.config import get_key_from_file_list
from recognition.utils import CTCLabelConverter, AttnLabelConverter
from recognition.model import Model
from recognition.dataset import RawCV2Dataset, RawDataset, AlignCollate
from recognition.textract import ConverToTextract


DEBUG = False

# The flask app for serving predictions
app = flask.Flask(__name__)
#device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
device = torch.device('cpu')
def str2bool(v):
    return v.lower() in ("yes", "y", "true", "t", "1")
#--------------------------初始化-------------------------------------------------
class Args_parser:
 
    def __init__(self):
        self.trained_model = '/opt/ml/code/weights/craft_mlt_25k.pth'
        self.text_threshold = 0.7
        self.low_text = 0.4
        self.link_threshold = 0.4
        self.cuda = False
        self.canvas_size = 1280
        self.mag_ratio = 1.5
        self.poly = False
        self.show_time = False
        self.refine = False
        self.refiner_model = False
        
        
        self.workers = 0    #main process
        self.batch_size = 64
        self.saved_model = '/opt/ml/model/TPS-ResNet-BiLSTM-Attn-Seed1111/best_accuracy.pth'
        
        self.batch_max_length = 40
        self.imgH = 32
        self.imgW = 280
        self.rgb = False
        self.character = '0123456789abcdefghijklmnopqrstuvwxyz'
        self.sensitive = True
        self.PAD = False
        
        self.Transformation = 'TPS'
        self.FeatureExtraction = 'ResNet'
        self.SequenceModeling = 'BiLSTM'
        self.Prediction = 'Attn'
        self.num_fiducial = 20
        self.input_channel = 1
        self.output_channel = 512
        self.hidden_size = 256
        self.label_file_list = 'sample_data/chars.txt'
        


def init_craft_net(args):
    print("-" * 50)
    print("init_craft_net")            
    net = CRAFT()     # initialize
    print('CRAFT Loading weights from checkpoint (' + args.trained_model + ')')
    if args.cuda:
        net.load_state_dict(copyStateDict(torch.load(args.trained_model)))
    else:
        net.load_state_dict(copyStateDict(torch.load(args.trained_model, map_location='cpu')))

    if args.cuda:
        net = net.cuda()
        net = torch.nn.DataParallel(net)
        cudnn.benchmark = False
    net.eval()

    return net

def init_recognition_model(args):

    """ model configuration """
    print("-"* 50)
    print("init_recognition_model")

    file_list = args.label_file_list.split(',')
    args.character = get_key_from_file_list(file_list)  
    print(args.character)


    cudnn.benchmark = True
    cudnn.deterministic = True
    args.num_gpu = torch.cuda.device_count()

    if 'CTC' in args.Prediction:
        converter = CTCLabelConverter(args.character)
    else:
        converter = AttnLabelConverter(args.character)
    args.num_class = len(converter.character)

    if args.rgb:
        args.input_channel = 3
    model = Model(args)
    print('model input parameters', args.imgH, args.imgW, args.num_fiducial, args.input_channel, args.output_channel,
          args.hidden_size, args.num_class, args.batch_max_length, args.Transformation, args.FeatureExtraction,
          args.SequenceModeling, args.Prediction)

    #model = torch.nn.DataParallel(model).to(device)

    if not os.path.exists(args.saved_model):
        print("[Error] model is not exists. [{}]".format(args.saved_model))
    # load model
    print('loading pretrained model from {}    device:{}'.format(args.saved_model, device))

    state_dict = torch.load(args.saved_model, map_location=lambda storage, loc: storage)

    new_state_dict = OrderedDict()
    key_length = len('module.')
    for k, v in state_dict.items():
        #print(k, v)
        name = k[key_length:] # remove `module.`
        new_state_dict[name] = v
    # load params
    model.load_state_dict(new_state_dict)
    model = model.to(device)

    # prepare data. two demo images from https://github.com/bgshih/crnn#run-demo
    alignCollate_demo = AlignCollate(imgH=args.imgH, imgW=args.imgW, keep_ratio_with_pad=args.PAD)
    # predict
    model.eval()
    return model, alignCollate_demo, converter

#--------------------------初始化  结束-------------------------------------------------



#--------------------------识别  开始-------------------------------------------------

def recongnize_image_file(args, image_file, output_dir):
    """
    遍历图片文件
    :param input_dir:
    :return:
    """

    temp_name = image_file.split('/')[-1].split('.')[0]

    textract_json = None
    label_file = os.path.join( output_dir, temp_name + '.txt')
    #print("label_file ", label_file)
    #print("output_dir  {}   label_file {}".format(output_dir, label_file))

    
    if os.path.exists(label_file):
        try:      
            textract_json = recongnize_sub_image_file(args, image_file, label_file, output_dir)
        except Exception as exception:
            print("【Error】 图片[{}]  没有解析成功 ".format(image_file))
            print('【Error】 exception  [{}]'.format(exception))
            traceback.print_exc()

    else:
        print("【Error】 图片[{}]  没有生成对应的label文件 [{}]".format(image_file, label_file))
    
    return textract_json
    

def recongnize_sub_image_file(args, image_file, label_file, output_dir):
    """
    识别一个大图片中的多个小图片， 并且放回json文件。 
    :param image_file:
    :param label_file:
    :return:
    """
    lines = []
    with open(label_file, 'r', encoding='utf-8') as f:
        for line in f:
            lines.append(line)
    lines = do_merge_box(lines)

    save_img = cv2.imread(image_file)

    image_obj_list = []

    for i, line in enumerate(lines):
        # Draw box around entire LINE
        points = line.replace("\n", '').split(',')
        left = int(points[0]) if int(points[6]) > int(points[0]) else int(points[6])
        right = int(points[2]) if int(points[4]) < int(points[2]) else int(points[4])
        top = int(points[1]) if int(points[3]) > int(points[1]) else int(points[3])
        bottom = int(points[5]) if int(points[7]) < int(points[5]) else int(points[7])
        height = bottom - top
        width = right - left

        c_img = save_img[top: int(top + height), left: int(left + width)]
        #new_height = 32
        #new_width = int(width * new_height / height)

        #print(" {} {}  new {} {}".format(width, height, new_width, new_height ) )
        #c_img=cv2.resize(c_img,(new_width, new_height))   
        new_image_file = os.path.join( output_dir,  str(i).zfill(6)+ '.jpg')

        #print("sub image: ", new_image_file)
        if DEBUG:
            cv2.imwrite(new_image_file, c_img)
        image_obj_list.append((new_image_file, c_img))


    # 补齐  batch_size
    
    print("识别了对象数量={}".format(len(image_obj_list)))

    demo_data = RawCV2Dataset(image_obj_list=image_obj_list, opt=args)  # use RawDataset

    demo_loader = torch.utils.data.DataLoader(
        demo_data, batch_size=args.batch_size,
        shuffle=False,
        num_workers=int(args.workers),
        drop_last = False,
        collate_fn=alignCollate_demo, pin_memory=False)    

    results = test_recong(args, model, demo_loader, converter, device)    

    #file_name_dest, image_file, lines
    new_lines = []
    #print("line length:  {}   result length: {} ".format(len(lines), len(results)))

    if len(results) > len(lines):
        results = results[0:len(lines)]


    for line, result in zip(lines, results) :
        new_line = '{},{:.4f},{}\n'.format(line.replace("\n", ''), float(result[2]), result[1] )
        new_lines.append(new_line)

    file_name_dest = os.path.join(output_dir, label_file.split('/')[-1].split('.')[0] +'.json' )
    converToTextract = ConverToTextract( file_name_dest, image_file, new_lines)
    textract_json = converToTextract.convert()
    print('【输出】生成json文件{}.   识别{}个文本'.format(file_name_dest, len(results)))
    #print(textract_json)
    
    return textract_json
        
    
    
#--------------------------识别 结束-------------------------------------------------



#----------------------------Main----------------------------------------------------------
def init_model():
    time_start = time.time()
    # Argument parsing

    # step 1. 初始化文本区域检测网络
    craft_net = init_craft_net(args)

    # step 2. 初始化文本识别网络
    model, alignCollate_demo, converter = init_recognition_model(args)

    time_elapsed = time.time() - time_start
    print('init model use time:  {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    return craft_net, model, alignCollate_demo, converter
    

def ocr_main(image_file, output_dir):

    #print("text_detection_single output_dir  ", output_dir)
    text_detection_single(image_file, craft_net, args, output_dir)
    textract_json = recongnize_image_file(args, image_file, output_dir)
    
    return textract_json
    

#----------------------------WEB  start-------------------------------------------------

@app.route('/ping', methods=['GET'])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""
    #health = boto3.client('s3') is not None  # You can insert a health check here

    #status = 200 if health else 404
    status = 200
    return flask.Response(response='\n', status=status, mimetype='application/json')


@app.route('/')
def hello_world():
    return 'ocr endpoint'


@app.route('/invocations', methods=['POST'])
def invocations():
    """Do an inference
    """
    
  
    data = None
    #解析json，
    if flask.request.content_type == 'application/json':
        data = flask.request.data.decode('utf-8')
        data = json.loads(data)
        print("  invocations params [{}]".format(data))
        bucket = data['bucket']
        image_uri = data['image_uri']
    else:
        return flask.Response(response='This predictor only supports JSON data', status=415, mimetype='text/plain')    
    
    download_file_name = image_uri.split('/')[-1]
    #s3_client.download_file(bucket, image_uri, download_file_name)

    tt = time.mktime(datetime.datetime.now().timetuple())

    args_verbose = False
    args_output_dir = os.path.join(init_output_dir,  str(int(tt)) + download_file_name.split('.')[0])
    args_input_file = download_file_name
 
    if not os.path.exists(args_output_dir):
        os.mkdir(args_output_dir)

    download_file_name = os.path.join(args_output_dir, download_file_name)
    s3_client.download_file(bucket, image_uri, download_file_name)
    
    print("download_file_name : {} ".format(download_file_name))
    inference_result = ocr_main(download_file_name, args_output_dir)

    
    _payload = json.dumps({'status': 400, 'message': 'ocr failed!'})
    if inference_result:
         _payload = json.dumps(inference_result)
    
    
    shutil.rmtree(args_output_dir)  
    
    return flask.Response(response=_payload, status=200, mimetype='application/json')




#---------------------------------------
init_output_dir = '/opt/ml/output_dir'

if not os.path.exists(init_output_dir):
    os.mkdir(init_output_dir)
else:
    print("-------------init_output_dir ", init_output_dir)
args = Args_parser()
s3_client = boto3.client('s3')
craft_net, model, alignCollate_demo, converter = init_model()
#---------------------------------------


if __name__ == '__main__':
    app.run()
    """
    print("server ------run")
    
    output_dir = os.path.join('./', 'temp')
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
        
    ocr_main('../../../sample_data/images/test.jpg', output_dir)
    """ 