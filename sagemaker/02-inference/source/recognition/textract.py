import json
import uuid
import cv2
import os

class ConverToTextract:
    def __init__(self, file_name_dest, image_file, lines):
        self.file_dest=file_name_dest
        self.lines = lines
        
        
        image = cv2.imread(image_file)
        size = image.shape
        w = size[1] #宽度
        h = size[0] #高度
        #print('{}   size = {}'.format(image_file, size))
        
        self.width=w
        self.height=h

    def __write_result(self,result):
        with open(self.file_dest, 'w', encoding='utf-8') as file:
            file.write(json.dumps(result))
            
            
    def convert(self):
        width=self.width
        height=self.height
        result = {"DocumentMetadata": {"Pages": 1}, "JobStatus": "SUCCEEDED"}
        block_page = {"BlockType": "PAGE",
                      "Geometry": {"BoundingBox": {"Width": 1.0, "Height": 1.0, "Left": 0.0, "Top": 0.0},
                                   "Polygon": [{"X": 0.0, "Y": 0.0}, {"X": 1.0, "Y": 0.0}, {"X": 1.0, "Y": 1.0},
                                               {"X": 0.0, "Y": 1.0}]}, "Id": str(uuid.uuid4())}

        lines = self.lines

        ids = []
        result["Blocks"] = [block_page]
        for line in lines:
            line = line.replace("\n", '')
            items = line.split(',')
            
            block_word = {"BlockType": "WORD"}
            block_word["Confidence"] = float(items[8])
            block_word["Text"] = ','.join(items[9:])
            BoundingBox = {"Width": float(int(items[2]) - int(items[0]))  / width, 
                           "Height": float(int(items[7]) - int(items[1])),
                           "Left": float(items[0]) / width, 
                           "Top": float(items[1]) / height}
            
            Polygon_0 = {"X": float(items[0]) / width, "Y": float(items[1]) / height}
            Polygon_1 = {"X": float(items[2]) / width, "Y": float(items[3]) / height}
            Polygon_2 = {"X": float(items[4]) / width, "Y": float(items[5]) / height}
            Polygon_3 = {"X": float(items[6]) / width, "Y": float(items[7]) / height}
            
            Polygon = [Polygon_0, Polygon_1, Polygon_2, Polygon_3]
            block_word["Geometry"] = {"BoundingBox": BoundingBox, "Polygon": Polygon}
            block_word_id = str(uuid.uuid4())
            block_word["Id"] = block_word_id
            block_word["Page"] = 1
            ids.append(block_word_id)
            result["Blocks"].append(block_word)

        block_page["Relationships"] = [{"Type": "CHILD", "Ids": ids}]
        block_page["Page"] = 1
        #self.__write_result(result)
        return result


if __name__ == "__main__":
    #convert=OCRConver('/home/ec2-user/tfc/031_ocr/ocr-craft-cn-pytorch/temp/output/demo001.txt','temp.json', '/home/ec2-user/tfc/031_ocr/ocr-craft-cn-pytorch/temp/output/demo001.jpg' )
    #convert.convert()
    print("main")