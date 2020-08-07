#!/bin/bash

echo $#  '生成中文数据集'
if [ $# -ne 3 ]
then
    echo "Usage: $0 '../sample_data/demo.txt'  0.2   ../output/"
    exit
fi

startTime=`date +%Y%m%d-%H:%M`
startTime_s=`date +%s`

BASE_DIR=$3

if [ ! -d ${BASE_DIR} ];then
mkdir ${BASE_DIR}
fi

export PYTHONPATH=./
echo "start --------- segment  string -- "
python3 ./segment_string.py -mi 14 -ma 14 -i $1 --output_dir ${BASE_DIR}

echo 'input file line count: '
wc -l $1

echo "start --------- generate  image --"
TOTAL_COUNT=$(wc -l ${BASE_DIR}'text_split.txt' | awk '{print $1}')

echo 'val_rate: ' $2 ' count ' ${TOTAL_COUNT}


val_count=`echo "scale=0; ${TOTAL_COUNT} * $2" | bc`
val_count=`echo $val_count | awk -F. '{print $1}'`

train_count=$[TOTAL_COUNT - val_count]

echo 'total  count: '  ${TOTAL_COUNT}
echo 'valid  count: '  ${val_count}
echo 'train  count: '  ${train_count}

head -n ${train_count} ${BASE_DIR}'text_split.txt'  > ${BASE_DIR}'train.txt'
tail -n ${val_count}   ${BASE_DIR}'text_split.txt'  > ${BASE_DIR}'valid.txt'


if [ ! -d ${BASE_DIR}"images" ]
then
    mkdir ${BASE_DIR}"images"
    mkdir ${BASE_DIR}"images/train"
    mkdir ${BASE_DIR}"images/valid"
fi
 
trdg \
-c $train_count -l cn -i ${BASE_DIR}'train.txt' -na 2 \
-rk \
-rbl \
--output_dir ${BASE_DIR}"images/train" -fd "./font/"


trdg \
-c $val_count -l cn -i ${BASE_DIR}'valid.txt' -na 2 \
-rk \
-rbl \
--output_dir ${BASE_DIR}"images/valid" -fd "./font/"


#head -n 20 ${BASE_DIR}"image_list_valid.txt"  > ${BASE_DIR}'image_list_test.txt'
 
echo "start --------- generate  lmdb "

python3 create_lmdb_dataset.py --inputPath ${BASE_DIR}"images/train" --gtFile ${BASE_DIR}"images/train/labels.txt" --outputPath ${BASE_DIR}"train"

python3 create_lmdb_dataset.py --inputPath ${BASE_DIR}"images/valid" --gtFile ${BASE_DIR}"images/valid/labels.txt" --outputPath ${BASE_DIR}"valid"




endTime=`date +%Y%m%d-%H:%M`
endTime_s=`date +%s`
echo "$startTime ---> $endTime"