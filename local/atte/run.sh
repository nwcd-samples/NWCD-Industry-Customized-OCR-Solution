#!/usr/bin/env bash
export PYTHONPATH=./

echo 'Train -------------------'
python3 train.py \
--train_data ../datasets/train \
--valid_data ../datasets/valid \
--select_data 'MJ-ST-EN-19-SP' \
--batch_ratio '0.4-0.1-0.2-0.15-0.15' \
--batch_size 160 \
--valInterval 200 \
--output 'saved_models' \
--label_file_list  'data/chars.txt' \
--Transformation TPS --FeatureExtraction ResNet --SequenceModeling BiLSTM --Prediction Attn \
--saved_model saved_models/TPS-ResNet-BiLSTM-Attn-Seed1111/best_accuracy.pth
