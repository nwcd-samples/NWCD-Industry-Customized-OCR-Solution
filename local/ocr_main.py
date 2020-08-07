import argparse
from multiprocessing import Pool
from pathlib import Path
from PIL import Image
import argparse
import shutil
import errno
import time
import uuid
import fitz
import json
import glob
import uuid
import cv2
import os
from collections import OrderedDict

import traceback
import torch
import torch.nn as nn
import torch.backends.cudnn as cudnn
from torch.autograd import Variable
from craft.craft import CRAFT
from craft.text_detection import text_detection 
from craft.text_detection import copyStateDict
from craft.merge_box import do_merge_box
from recognition.recognition import test_recong
from recognition.config import get_key_from_file_list
from recognition.utils import CTCLabelConverter, AttnLabelConverter
from recognition.model import Model
from recognition.dataset import RawCV2Dataset, RawDataset, AlignCollate
from recognition.textract import ConverToTextract



DEBUG = True

# 选择GPU 还是CPU进行训练
#device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
device = torch.device('cpu')

def str2bool(v):
    return v.lower() in ("yes", "y", "true", "t", "1")

class OcrMain(object):
    """

    python3 craft_label_parser.py  -i ../dataset/raw -o ../dataset/output

    """

    def __init__(self):
        args = self.parse_arguments()
        self.output_dir = args.output_dir
        self.input_dir = args.input_dir
        self.image_files = []

    def parse_arguments(self):
        """
            Parse the command line arguments of the program.
        """

        parser = argparse.ArgumentParser(
            description="Textract 中文版本"
        )
        parser.add_argument("-o","--output_dir",type=str,nargs="?",help="输出文件的本地路径",required=True)
        parser.add_argument("-i","--input_dir",type=str,nargs="?",help="输入文件路径",required=True)
        # Detection model  检测模型
        parser.add_argument('--trained_model', default='weights/craft_mlt_25k.pth', type=str, help='pretrained model')
        parser.add_argument('--text_threshold', default=0.7, type=float, help='text confidence threshold')
        parser.add_argument('--low_text', default=0.4, type=float, help='text low-bound score')
        parser.add_argument('--link_threshold', default=0.4, type=float, help='link confidence threshold')
        parser.add_argument('--cuda', default=True, type=str2bool, help='Use cuda for inference')
        parser.add_argument('--canvas_size', default=1280, type=int, help='image size for inference')
        parser.add_argument('--mag_ratio', default=1.5, type=float, help='image magnification ratio')
        parser.add_argument('--poly', default=False, action='store_true', help='enable polygon type')
        parser.add_argument('--show_time', default=False, action='store_true', help='show processing time')
        parser.add_argument('--refine', default=False, type=str2bool,  help='enable link refiner')
        parser.add_argument('--refiner_model', default='weights/craft_refiner_CTW1500.pth', type=str, help='pretrained refiner model')

        
        # recognition model 识别模型
        parser.add_argument('--image_folder', default='/home/ec2-user/tfc/031_ocr/ocr-craft-cn-pytorch/recognition/temp/',   help='path to image_folder which contains text images')
        parser.add_argument('--workers', type=int, help='number of data loading workers', default=4)
        parser.add_argument('--batch_size', type=int, default=64, help='input batch size')
        parser.add_argument('--saved_model', required=True, help="path to saved_model to evaluation")
        """ Data processing """
        parser.add_argument('--batch_max_length', type=int, default=40, help='maximum-label-length')
        parser.add_argument('--imgH', type=int, default=32, help='the height of the input image')
        parser.add_argument('--imgW', type=int, default=280, help='the width of the input image')
        parser.add_argument('--rgb', action='store_true', help='use rgb input')
        parser.add_argument('--character', type=str, default='0123456789abcdefghijklmnopqrstuvwxyz', help='character label')
        parser.add_argument('--sensitive', action='store_true', default=True,  help='for sensitive character mode')
        parser.add_argument('--PAD', action='store_true', help='whether to keep ratio then pad for image resize')
        """ Model Architecture """
        parser.add_argument('--Transformation', type=str, required=True, help='Transformation stage. None|TPS')
        parser.add_argument('--FeatureExtraction', type=str, required=True, help='FeatureExtraction stage. VGG|RCNN|ResNet')
        parser.add_argument('--SequenceModeling', type=str, required=True, help='SequenceModeling stage. None|BiLSTM')
        parser.add_argument('--Prediction', type=str, required=True, help='Prediction stage. CTC|Attn')
        parser.add_argument('--num_fiducial', type=int, default=20, help='number of fiducial points of TPS-STN')
        parser.add_argument('--input_channel', type=int, default=1, help='the number of input channel of Feature extractor')
        parser.add_argument('--output_channel', type=int, default=512,
                            help='the number of output channel of Feature extractor')
        parser.add_argument('--hidden_size', type=int, default=256, help='the size of the LSTM hidden state')
        parser.add_argument('--label_file_list', type=str, required=True, help='label_file_list')
        parser.add_argument('--generate_train_data_dir', type=str, default='', help='生成训练数据的文件夹')
        parser.add_argument('--generate_train_confidence', type=float, default=0.90, help='低于阈值置信度的图片， 进行人工标注，然后训练')
        
        return parser.parse_args()

        
    def init_output_dir(self):
        
        """
        初始化图片列表  self.image_files
        生成临时文件夹， 保存原始图片 和裁剪的图片, 生成json文件
        FIXME: 正式环境， 全部到内存中进行
        :param input_dir:
        :param output_dir:
        :return:
        """
        # the tuple of file types
        types = ('*.jpg', '*.png', '*.jpeg', '*.JPG', '*.PNG', '*.JPEG')
        files_grabbed = []
        for files in types:
            files_grabbed.extend(glob.glob(os.path.join(self.input_dir, files)))

        # 给每个图片建立子文件夹 ， 用于存放临时生成的小图片
        for index, image_file in enumerate(files_grabbed):
            temp_name = image_file.split("/")[-1].split('.')[0]
            os.makedirs(os.path.join(self.output_dir, temp_name))
            
            self.image_files.append(image_file)  #所有的原始图片 保存到image_files中
        #print("初始化完成， 共有{}张图片".format(len(self.image_files)))
        
    
        #生成用于训练的小图片文件夹
        if not self.args.generate_train_data_dir == '':
            if os.path.exists(self.args.generate_train_data_dir):
                shutil.rmtree(self.args.generate_train_data_dir)
            os.makedirs(self.args.generate_train_data_dir)     
    
    
    def init_craft_net(self):
        """
        初始化 文本区域检测网络
        """        
        net = CRAFT()     # initialize
        print('CRAFT Loading weights from checkpoint (' + self.args.trained_model + ')')
        if self.args.cuda:
            net.load_state_dict(copyStateDict(torch.load(self.args.trained_model)))
        else:
            net.load_state_dict(copyStateDict(torch.load(self.args.trained_model, map_location='cpu')))

        if self.args.cuda:
            net = net.cuda()
            net = torch.nn.DataParallel(net)
            cudnn.benchmark = False
        net.eval()
        
        return net
    
    
    def init_recognition_model(self):
        
        """
        初始化文字识别模型
        """

        file_list = self.args.label_file_list.split(',')
        self.args.character = get_key_from_file_list(file_list)  


        cudnn.benchmark = True
        cudnn.deterministic = True
        self.args.num_gpu = torch.cuda.device_count()

        if 'CTC' in self.args.Prediction:
            self.converter = CTCLabelConverter(self.args.character)
        else:
            self.converter = AttnLabelConverter(self.args.character)
        self.args.num_class = len(self.converter.character)

        if self.args.rgb:
            self.args.input_channel = 3
        model = Model(self.args)
        print('model input parameters', self.args.imgH, self.args.imgW, self.args.num_fiducial, self.args.input_channel, self.args.output_channel,
              self.args.hidden_size, self.args.num_class, self.args.batch_max_length, self.args.Transformation, self.args.FeatureExtraction,
              self.args.SequenceModeling, self.args.Prediction)
        
        #model = torch.nn.DataParallel(model).to(device)

        # load model
        print('loading pretrained model from {}    device:{}'.format(self.args.saved_model, device))
        
        state_dict = torch.load(self.args.saved_model, map_location=lambda storage, loc: storage)
        
        new_state_dict = OrderedDict()
        key_length = len('module.')
        for k, v in state_dict.items():
            name = k[key_length:] # remove `module.`
            new_state_dict[name] = v
        # load params
        model.load_state_dict(new_state_dict)
        model = model.to(device)
        
        # prepare data. two demo images from https://github.com/bgshih/crnn#run-demo
        self.AlignCollate_demo = AlignCollate(imgH=self.args.imgH, imgW=self.args.imgW, keep_ratio_with_pad=self.args.PAD)
        # predict
        model.eval()
        return model
    


    def recongnize_image_file(self):
        """
        遍历图片文件
        :param input_dir:
        :param output_dir:
        :return:
        """
     
        # 遍历所有图片文件
        for index, image_file in enumerate(self.image_files):

            temp_name = image_file.split('/')[-1].split('.')[0]
            sub_image_dir = os.path.join(self.output_dir, temp_name)

            label_file = os.path.join( self.output_dir, temp_name + '.txt')
            #print("label_file ", label_file)
            
            if os.path.exists(label_file):
                try:      
                    self.recongnize_sub_image_file(image_file, label_file, sub_image_dir)
                except Exception as e:
                    print("【Error】 图片[{}]  没有解析成功 ".format(image_file))
                    print('traceback.format_exc():\n%s' % traceback.format_exc())
                    
            
            else:
                print("【Error】 图片[{}]  没有生成对应的label文件 [{}]".format(image_file, label_file))

        print("共解析{}个图片文件".format(len(self.image_files)))





    def recongnize_sub_image_file(self, image_file, label_file, sub_image_dir):
        """
        识别一个大图片中的多个小图片， 并且放回json文件。 
        :param image_file:
        :param label_file:
        :param sub_image_dir:
        :return:
        """
        with open(label_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
                
        # 进行文本区域的合并， 有一些比较接近的小区域，合并成较大区域        
        lines = do_merge_box(lines)

        save_img = cv2.imread(image_file)

        image_obj_list = []
        
        randam_id = str(uuid.uuid4())
        randam_id = ''.join(randam_id.split('-'))[0:5]
        
        for i, line in enumerate(lines):
            # Draw box around entire LINE
            #print("{}   {}".format(i , line))
            points = line.replace("\n", '').split(',')
            # 计算四个顶点
            left = int(points[0]) if int(points[6]) > int(points[0]) else int(points[6])
            right = int(points[2]) if int(points[4]) < int(points[2]) else int(points[4])
            top = int(points[1]) if int(points[3]) > int(points[1]) else int(points[3])
            bottom = int(points[5]) if int(points[7]) < int(points[5]) else int(points[7])
            height = bottom - top
            width = right - left
            #print("index= {:4d}    top={} bottom={} left={} right={}".format(i, top, bottom, left, right))
            c_img = save_img[top: bottom, left: right]

            # 图片resize, 可以不使用， 网络会进行缩放
            new_height = self.args.imgH
            new_width = int(width * new_height / height)
            #c_img=cv2.resize(c_img,(new_width, new_height)) 
            
            #print(" {} {}  new {} {}".format(width, height, new_width, new_height ) )
            #new_image_file = os.path.join( sub_image_dir,  str(i).zfill(6)+ '.jpg')
            train_image_file = '{}_{}_{}.jpg'.format(sub_image_dir.split('/')[-1], randam_id, str(i).zfill(5))
            train_image_file = os.path.join(self.args.generate_train_data_dir, train_image_file)
            if not self.args.generate_train_data_dir == '':
                cv2.imwrite(train_image_file, c_img)
            image_obj_list.append((train_image_file, c_img))

            
        #如果用多GPU进行推理  需要补齐batch_size， 重复复制最后一个图片， 让list 数量可以整除batch size
        """
        if len(image_obj_list) >  self.args.batch_size and  len(image_obj_list) % self.args.batch_size !=0:
            for item in range(self.args.batch_size - len(image_obj_list) % self.args.batch_size):
                image_obj_list.append(image_obj_list[-1])
        """
        
        print("image_obj_list  length: ", len(image_obj_list))
            
        demo_data = RawCV2Dataset(image_obj_list=image_obj_list, opt=self.args)  # use RawDataset
        #demo_data = RawDataset(root=sub_image_dir, opt=self.args)
        
        demo_loader = torch.utils.data.DataLoader(
            demo_data, batch_size=self.args.batch_size,
            shuffle=False,
            num_workers=int(self.args.workers),
            drop_last = False,
            collate_fn=self.AlignCollate_demo, pin_memory=False)    
            
        # 进行文字识别    
        results = test_recong(self.args, self.model, demo_loader,self.converter, device)    

        #file_name_dest, image_file, lines
        new_lines = []
        #print("line length:  {}   result length: {} ".format(len(lines), len(results)))
        
        # 如果用多GPU进行推理, 删除掉多余的补齐数据
        if len(results) > len(lines):
            results = results[0:len(lines)]
            
        total_socre= 0.0
        train_label_txt = ''
        for line, result in zip(lines, results) :
            new_line = '{},{:.4f},{}\n'.format(line.replace("\n", ''), float(result[2]), result[1] )
            total_socre += float(result[2])
            new_lines.append(new_line)
            # 生成训练的label文件
            if float(result[2]) < self.args.generate_train_confidence:
                train_label_txt += '{} {}\n'.format(result[0].split('/')[-1], result[1])
            else:
                if not self.args.generate_train_data_dir == '':   
                    os.remove(result[0])
        # 生成训练的label文件
        if not self.args.generate_train_data_dir == '':    
            with open(os.path.join(self.args.generate_train_data_dir, 'labels.txt'), 'a', encoding='utf-8') as file:
                file.write(train_label_txt)
        
        
        
        #生成Textract 格式数据
        file_name_dest = os.path.join(self.output_dir, label_file.split('/')[-1].split('.')[0] + '.json' )
        converToTextract = ConverToTextract( file_name_dest, image_file, new_lines)
        converToTextract.convert()
        
        mean_socre = total_socre/len(results)   #平均置信度
        print('【输出】生成json文件{}.   识别{}个文本, 平均得分 {:.4f}'.format(file_name_dest, len(results), mean_socre))
        

    def main(self):
        time_start = time.time()
        # Argument parsing
        
        args = self.parse_arguments()
        self.args = args
        if os.path.exists(args.output_dir):
            shutil.rmtree(args.output_dir)
            
            pass

        try:
            os.makedirs(args.output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        if not os.path.exists(args.input_dir):
            print("输入路径不能为空  input_dir[{}] ".format(args.input_dir))
            return
        
        if  os.path.exists(os.path.join(args.input_dir, 'ipynb_checkpoints')):
            shutil.rmtree(os.path.join(args.input_dir, 'ipynb_checkpoints'))
        
        # step 1. 初始化文本区域检测网络
        self.net = self.init_craft_net()

        
        # step 2. 初始化文本识别网络
        self.model = self.init_recognition_model()
        
        # step 3 . 生成初始化文件夹
        self.init_output_dir()
        
        
        # step 4. 检测文本区域, 生成对应的label文件
        text_detection( self.args, self.net)
        
        # step 5. 切分小图图片, 进行预测
        self.recongnize_image_file()

        # step 6. 清理工作
        
        #if not DEBUG:
            
        
        
        time_elapsed = time.time() - time_start
        print('The code run {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))



if __name__ == "__main__":
    ocrMain = OcrMain()
    ocrMain.main()