# coding:utf-8

import os
import glob


def get_key_from_file_list(file_list):
    #file_list = glob.glob(os.path.join(input_dir, '*.txt'))

    print('get_key_from_file_list() file_list : ', file_list)

    content = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-~`<>'.:;^/|!?$%#@&*()[]{}_+=,\\\""
    for file_name in file_list:
        with open(file_name, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                content += line

    content = content.replace('\n', '')
    content = content.replace('\t', '')
    char_list = list(set(content))
    char_list.sort()
    content = content.replace(' ', '')
    content = ''.join(char_list)
    #print("-"*30)
    #print('class nums: ',  len(content)+1)
    #print(content)
    #print("-"*30)
    return content
    #return "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-~`<>'.:;^/|!?$%#@&*()[]{}_+=,\\\""



#CHAR_VECTOR = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-~`<>'.:;^/|!?$%#@&*()[]{}_+=,\\\""
#NUM_CLASSES = len(CHAR_VECTOR) + 1
