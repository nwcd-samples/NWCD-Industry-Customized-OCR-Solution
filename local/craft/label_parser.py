import argparse
from multiprocessing import Pool
from pathlib import Path
from PIL import Image
import argparse
import shutil
import errno
import time
import uuid
import json
import glob
import cv2
import os




class CraftParser(object):
    """

    python3 craft_label_parser.py  -i ../dataset/raw -o ../dataset/output

    """

    def __init__(self):
        args = self.parse_arguments()
        self.output_dir = args.output_dir
        self.input_dir = args.input_dir

    def parse_arguments(self):
        """
            Parse the command line arguments of the program.
        """

        parser = argparse.ArgumentParser(
            description="对图片中的文字区域进行裁剪"
        )
        parser.add_argument(
            "-o",
            "--output_dir",
            type=str,
            nargs="?",
            help="输出文件的本地路径",
            required=True
        )
        parser.add_argument(
            "-i",
            "--input_dir",
            type=str,
            nargs="?",
            help="输入文件路径",
            required=True
        )
        return parser.parse_args()



    def read_local_image_file(self, input_dir, output_dir):
        """
        生成临时文件夹， 保存原始图片 json 和裁剪的图片
        :param input_dir:
        :param output_dir:
        :return:
        """
        # the tuple of file types
        types = ('*.jpg', '*.png', '*.jpeg', '*.JPG', '*.PNG', '*.JPEG')
        files_grabbed = []
        for files in types:
            files_grabbed.extend(glob.glob(os.path.join(input_dir, files)))



        for index, image_file in enumerate(files_grabbed):
            suid = ''.join(str(uuid.uuid4()).split('-'))

            file_output_dir = os.path.join(output_dir,
                                           image_file.split('/')[-1].replace('.', '_').replace('.', '') + '_' + suid[0:8])

            os.makedirs(file_output_dir)


            label_file = os.path.join( input_dir, image_file.split('/')[-1].split('.')[0] +'.txt')

            if os.path.exists(label_file):
                self.create_gt_image_label(image_file, label_file, file_output_dir)

        print("共有文件{}个".format(len(files_grabbed)))





    def create_gt_image_label(self, image_file, label_file, output_dir):
        """

        :param image_file:
        :param label_file:
        :param output_dir:
        :return:
        """
        lines = []
        with open(label_file, 'r', encoding='utf-8') as f:
            for line in f:
                lines.append(line)

        shutil.copyfile(label_file, output_dir)
        save_img = cv2.imread(image_file)

        save_path = os.path.join(output_dir, 'images')
        Path(save_path).mkdir(parents=True, exist_ok=True)

        gt_labels = ""
        # save image bounding box/polygon the detected lines/text
        for i, line in enumerate(lines):
            # Draw box around entire LINE
            points = line.replace("\n", '').split(',')
            left = int(points[0])
            top = int(points[1])
            width = int(points[2]) - int(points[0])
            height = int(points[7]) - int(points[1])
            c_img = save_img[top: int(top + height), left: int(left + width)]


            new_image_file = output_dir.split('/')[-1]+'_'+str(i).zfill(3)+ '.' + image_file.split('.')[-1]

            print('new_image_file: ', new_image_file)
            f = os.path.join(save_path, new_image_file)
            cv2.imwrite(f, c_img)

            colors = (0, 0, 0)
            cv2.rectangle(save_img, (left, top), (left+width, top+height), colors, 1)

        label_image_file = os.path.join(output_dir, 'image_label.'+image_file.split('.')[-1])
        #cv2.imwrite(label_image_file, save_img)
        print('【输出】生成合格后的图片{} .'.format(label_image_file))


    def main(self):
        time_start = time.time()
        # Argument parsing
        args = self.parse_arguments()
        if os.path.exists(args.output_dir):
            shutil.rmtree(args.output_dir)

        try:
            os.makedirs(args.output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        if not os.path.exists(args.input_dir):
            print("输入路径不能为空  input_dir[{}] ".format(args.input_dir))
            return
        # step 1 . 生成文件夹
        self.read_local_image_file(args.input_dir, args.output_dir)



        # step 2. OCR
        # self.parse_file_list(args.segment_flag)

        time_elapsed = time.time() - time_start
        print('The code run {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))



if __name__ == "__main__":
    craftParser = CraftParser()
    craftParser.main()