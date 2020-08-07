#!/usr/bin/env bash


if [ ! -d "../local/atte/saved_models/TPS-ResNet-BiLSTM-Attn-Seed1111" ]; then
  mkdir ../local/atte/saved_models/TPS-ResNet-BiLSTM-Attn-Seed1111 -p
fi

if [ ! -f ../local/atte/saved_models/TPS-ResNet-BiLSTM-Attn-Seed1111/best_accuracy.pth ]; then
    echo 'Download  best_accuracy.pth ......'
    cd ../local/atte/saved_models/TPS-ResNet-BiLSTM-Attn-Seed1111/
    wget https://dikers-public.s3.cn-northwest-1.amazonaws.com.cn/model/ocr/best_accuracy.pth
    cd -
fi



if [ ! -d '../local/craft/weights' ]; then
    mkdir -p ../local/craft/weights
fi

if [ ! -f ../local/craft/weights/craft_mlt_25k.pth ]; then
    echo 'Download  craft_mlt_25k.pth ......'
    cd ../local/craft/weights
    wget https://dikers-public.s3.cn-northwest-1.amazonaws.com.cn/model/ocr/craft_mlt_25k.pth
    cd -
fi


export PYTHONPATH=../

python3 ../local/ocr_main.py  \
-i '../local/sample_data/images/' \
-o 'output/' \
--cuda==False  \
--batch_size 64 \
--label_file_list  '../local/sample_data/chars.txt' \
--Transformation TPS --FeatureExtraction ResNet --SequenceModeling BiLSTM --Prediction Attn \
--saved_model ../local/atte/saved_models/TPS-ResNet-BiLSTM-Attn-Seed1111/best_accuracy.pth \
--trained_model ../local/craft/weights/craft_mlt_25k.pth \
--generate_train_data_dir 'output/train/' \
--generate_train_confidence=0.90