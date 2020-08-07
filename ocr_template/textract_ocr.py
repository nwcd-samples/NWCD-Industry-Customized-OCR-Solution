# -*-coding:utf8-*-
"""
author: liangzhang@nwcdcloud.cn
1. 读取本地文件夹的PDF 文件
2. 将pdf 上传到Global S3中
3. 对Global S3 中的文件 调用AWS Textract 服务
4. 将返回结果保存到本地
5. 将本地文件上传到国内服务器上， 并且打开访问权限， 供测试使用

"""
import boto3
import json
import os
import glob
import time
import shutil
import errno
import argparse

class TextOcrUtil:

    def __init__(self,  profile_name, bucket_name, output_dir):
        """
            初始化
        """
        boto3.setup_default_session(profile_name=profile_name)
        print("----init start")
        self._textract = boto3.client('textract')
        self._s3 = boto3.client('s3')
        self._bucket_name = bucket_name
        print("----init end")
        self._output_dir = output_dir


    def parse_file_list(self, input_dir, s3_file_prefix):
        """
        调用Textract 进行文本识别
        :param pdf_file_path:
        :param s3_file_prefix:
        :return:
        """
        print(" parse file path: {} ".format(input_dir))
        types = ('*.pdf', '*.jpg', '*.png', '*.jpeg')
        file_names = []
        for files in types:
            file_names.extend(glob.glob(os.path.join(input_dir, files)))

        print("File list length: {} ".format(len(file_names)))
        json_file_list = []
        for file_name in file_names:

            print("parse file: {} ".format(file_name))
            new_file_name = file_name.split('/')[-1].split('.')[0]
            postfix = file_name.split('/')[-1].split('.')[1]


            upload_data = open(file_name, mode='rb')

            key = s3_file_prefix + '/' + new_file_name+'.'+postfix
            file_obj = self._s3.put_object(Bucket=self._bucket_name,
                                           Key=key,
                                           Body=upload_data, Tagging='ocr')
            print('Upload pdf {}  返回结果: {}'.format(new_file_name, file_obj))

            response = self._textract.start_document_analysis(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': self._bucket_name,
                        'Name': key
                    }
                },
                FeatureTypes=['TABLES', 'FORMS']
            )
            status = 'IN_PROGRESS'

            while status == 'IN_PROGRESS':
                time.sleep(5)
                # print("file_name {} ------------------status {}  ".format(file_name, status))
                status = self._textract.get_document_analysis(JobId=response['JobId'])['JobStatus']

                if status != 'IN_PROGRESS':
                    json_file = os.path.join(self._output_dir, new_file_name+'.json')
                    with open(json_file, 'w') as f:
                        f.write(json.dumps(self._textract.get_document_analysis(JobId=response['JobId'])))

                    print("Save json to local [{}] ".format(json_file))
                    json_file_list.append((json_file, new_file_name+'.json'))

        return json_file_list

    def upload_json_file_to_cn(self, json_file_list, profile_name, bucket_name, s3_json_file_prefix):
        """
        将文件上传到国内s3 中
        :param json_file_list:
        :param profile_name:
        :param bucket_name:
        :param s3_json_file_prefix:
        :return:
        """

        boto3.setup_default_session(profile_name=profile_name)
        s3 = boto3.client('s3')

        for item in json_file_list:

            json_file = item[0]
            file_name = item[1]
            upload_data = open(json_file, mode='rb')

            key = s3_json_file_prefix + file_name
            file_obj = s3.put_object(Bucket=bucket_name, Key=key, Body=upload_data, Tagging='ocr')
            s3.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=key)
            print("Upload json 返回结果: {} ".format(file_obj))
            print("https://{}.s3.cn-northwest-1.amazonaws.com.cn/{}\n".format(bucket_name, key))


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
        self.output_dir = args.output_dir
        self.global_profile_name = args.global_profile_name
        self.global_s3_name = args.global_s3_name

        if not os.path.exists(args.input_dir):
            print("输入路径不能为空  input_dir[{}] ".format(args.input_dir))
            return
        # step 1 . 生成文件夹
        self.read_local_image_file(args.input_dir, args.output_dir)

        # step 2 .  textract

        self.parse_file_list(args.prefix_s3)

        # step 3 .  切分图片按

        for file_item in self.file_map.items():
            file_output_path = file_item[0]
            self.cut_one_img(file_output_path)

        # step 4 . copy 到国内s3 上


        # Create the directory if it does not exist.

        time_elapsed = time.time() - time_start
        print('The code run {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))



if __name__ == "__main__":

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
    parser.add_argument(
        "-p",
        "--prefix_s3",
        type=str,
        nargs="?",
        help="s3 保存文件的前缀",
        required=True
    )

    parser.add_argument(
        "-gs",
        "--global_s3_name",
        type=str,
        nargs="?",
        help="AWS 全球 s3",
        required=True
    )
    parser.add_argument(
        "-gp",
        "--global_profile_name",
        type=str,
        nargs="?",
        help="AWS 全球 profile name ",
        required=True
    )

    parser.add_argument(
        "-cs",
        "--cn_s3_name",
        type=str,
        nargs="?",
        help="国内 s3",
        required=True
    )
    parser.add_argument(
        "-cp",
        "--cn_profile_name",
        type=str,
        nargs="?",
        help="AWS 国内 profile name ",
        required=True
    )
    time_start = time.time()

    args = parser.parse_args()
    text_ocr_utl = TextOcrUtil(args.global_profile_name, args.global_s3_name, args.output_dir)

    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)
    os.makedirs(args.output_dir)


    json_file_list = text_ocr_utl.parse_file_list(args.input_dir, args.prefix_s3)
    text_ocr_utl.upload_json_file_to_cn(json_file_list, args.cn_profile_name,
                                        args.cn_s3_name,  args.prefix_s3)



    # Create the directory if it does not exist.

    time_elapsed = time.time() - time_start
    print('The code run {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))