import string
import argparse

import torch
import torch.backends.cudnn as cudnn
import torch.utils.data
import torch.nn.functional as F

from recognition.utils import CTCLabelConverter, AttnLabelConverter
from recognition.dataset import RawDataset, AlignCollate
from recognition.model import Model
from recognition.config import get_key_from_file_list

def test_recong(opt, model, demo_loader, converter, device):
    
    
    with torch.no_grad():
        
        
        results = [] 
        for image_tensors, image_path_list in demo_loader:
            batch_size = image_tensors.size(0)
            image = image_tensors.to(device)
            # For max length prediction
            length_for_pred = torch.IntTensor([opt.batch_max_length] * batch_size).to(device)
            text_for_pred = torch.LongTensor(batch_size, opt.batch_max_length + 1).fill_(0).to(device)
           
            if 'CTC' in opt.Prediction:
                preds = model(image, text_for_pred)

                # Select max probabilty (greedy decoding) then decode index to character
                preds_size = torch.IntTensor([preds.size(1)] * batch_size)
                _, preds_index = preds.max(2)
                #FIXME:  edit by dikers issue （https://github.com/clovaai/deep-text-recognition-benchmark/issues/185）
                #preds_index = preds_index.view(-1)
                preds_str = converter.decode(preds_index.data, preds_size.data)

            else:
                preds = model(image, text_for_pred, is_train=False)

                # select max probabilty (greedy decoding) then decode index to character
                _, preds_index = preds.max(2)
                preds_str = converter.decode(preds_index, length_for_pred)


            dashed_line = '-' * 110
            head = f'{"image_path":50s}\t{"predicted_labels":30s}\tconfidence score'
            
            print(f'{dashed_line}\n{head}\n{dashed_line}')

            preds_prob = F.softmax(preds, dim=2)
            preds_max_prob, _ = preds_prob.max(dim=2)
            for img_name, pred, pred_max_prob in zip(image_path_list, preds_str, preds_max_prob):
                pred = format_string(pred)
                if 'Attn' in opt.Prediction:
                    pred_EOS = pred.find('[s]')
                    pred = pred[:pred_EOS]  # prune after "end of sentence" token ([s])
                    pred_max_prob = pred_max_prob[:pred_EOS]

                # calculate confidence score (= multiply of pred_max_prob)
                confidence_score = 0.0
                if len(pred_max_prob.cumprod(dim=0)) > 0:
                    confidence_score = pred_max_prob.cumprod(dim=0)[-1]

                print(f'{img_name:50s}\t{pred:30s}\t{confidence_score:0.4f}')
                results.append((img_name, pred, confidence_score))
                
                
                
    return results
 
    
    
def merge_spe_char(pred, spec, new_spec):
    index = pred.find(spec)
    new_pred = ''
    if index>0 and index < len(pred)-1:
        if pred[index-1].isdigit() and pred[index+1].isdigit():
            new_pred = '{}.{}'.format(pred[0:index],pred[index+1:])
            return new_pred
        
    return pred      

def format_string(pred):
    # !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~°±·×àé÷üαβγδωОПР–—―‘’“”…‰′※℃ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪ→↓∈√∩∵∶≠≤≥①②③④⑤⑥⑦⑧⑨⑩⑴⑵⑶⑾⑿⒀⒂⒃⒄⒅⒆⒉─━│┌┐╱■□▲△◆◇○◎●★☆、。〇〈〉《》「」『』【】〔〕
    pred = pred.replace('．', '.').lstrip().rstrip()
    pred = pred.replace('∶', ':').replace('︰', ':').replace('：', ':')
    pred = pred.replace('﹐', ',')
    pred = pred.replace('？', '?').replace('﹖', '?')
    pred = pred.replace('～', '~').replace('﹑', '、')
    pred = pred.replace('２', '2').replace('Ａ', 'A').replace('C', 'C')
    pred = pred.replace('；', ';').replace('﹔', ';')
    pred = pred.replace('，',',').replace('－', '-').replace('！', '!').replace('＋', '+')
    pred = pred.replace('）', ')').replace('（', '(').replace('○','0')
    pred = merge_spe_char(pred,'。', '.')
    pred = merge_spe_char(pred,'、', '.')
    pred = merge_spe_char(pred,'一', '-')
    return pred