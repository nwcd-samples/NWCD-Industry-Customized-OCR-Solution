export PYTHONPATH=../

python ../ocr_template/textract_ocr.py \
--input_dir='../input/' \
--output_dir='../output/' \
--prefix_s3='ocr_ouput' \
--global_s3_name='your_global_bucket_name' \
--global_profile_name='your_global_profile_name' \
--cn_s3_name='your_cn_s3_name' \
--cn_profile_name='your_cn_profile_name'
