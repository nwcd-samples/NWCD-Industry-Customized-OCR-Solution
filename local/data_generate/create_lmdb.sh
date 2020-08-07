python3 create_lmdb_dataset.py --inputPath /home/ec2-user/tfc/031_ocr/text_renderer/output/default/ \
--gtFile /home/ec2-user/tfc/031_ocr/text_renderer/output/valid.txt \
--outputPath ./output/valid

python3 create_lmdb_dataset.py --inputPath /home/ec2-user/tfc/031_ocr/text_renderer/output/default/  \
--gtFile /home/ec2-user/tfc/031_ocr/text_renderer/output/train.txt \
--outputPath ./output/train


