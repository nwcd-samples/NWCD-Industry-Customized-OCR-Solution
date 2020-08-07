
def _box_to_line(box):
    return '{},{},{},{},{},{},{},{}'.format(
        box['left'],
        box['top'],
        box['right'],
        box['top'],
        box['right'],
        box['bottom'],
        box['left'],
        box['bottom'],)

def _delete_row_in_list(new_lines, line):

    for index, new_line in enumerate(new_lines):
        if line == new_line:
            new_lines.remove(line)
            break


def _do_merge_inline(new_lines):

    box_list = []
    box_map = {}
    new_lines.sort()
    # 生成合并的box 框
    for index, line in enumerate(new_lines):
        line = line.replace("\n", '')
        #print('index {}    [{}]'.format(index, line))
        points = line.split(',')
        if len(points) < 8:
            continue
        box = {
            'left': int(points[0]),
            'right': int(points[2]),

            'width': int(points[2]) - int(points[0]),
            'height': int(points[7]) - int(points[1]),

            'top': int(points[1]),
            'bottom': int(points[7])
        }
        box_list.append(box)
        box_map[_box_to_line(box)] = False

    # for line in new_lines:
    #     print(line)

    # 查找临近的box， 本次合并的box 数量
    total_count = 0

    new_box_lines = []
    for i in range(len(box_list)):
        if box_map[_box_to_line(box_list[i])]:
            continue

        merge_flag = False

        for j in range(len(box_list)):
            if box_map[_box_to_line(box_list[j])] or i == j:
                continue
            if box_list[j]['width'] < 150 \
                    and abs(box_list[j]['left'] - box_list[i]['right']) < 9 \
                    and abs(box_list[j]['top'] - box_list[i]['top']) < 8 \
                    and abs(box_list[j]['bottom'] - box_list[i]['bottom']) < 8:

                # 添加新的box ， 删除两个旧的box

                top = box_list[i]['top']
                if box_list[j]['top'] < box_list[i]['top']:
                    top = box_list[j]['top']

                bottom = box_list[i]['bottom']
                if box_list[j]['bottom'] > box_list[i]['bottom']:
                    bottom = box_list[j]['bottom']


                new_box = {
                    'left': box_list[i]['left'],
                    'right': box_list[j]['right'],

                    'width': box_list[j]['right'] - box_list[i]['left'],
                    'height': bottom - top,

                    'top': top,
                    'bottom': bottom
                }

                box_map[_box_to_line(box_list[i])] = True
                box_map[_box_to_line(box_list[j])] = True
                _delete_row_in_list(new_box_lines, _box_to_line(box_list[i]))
                _delete_row_in_list(new_box_lines, _box_to_line(box_list[j]))
                new_box_lines.append(_box_to_line(new_box))
                merge_flag = True

                # print(' 合并  {} === {} '.format(box_to_line(box_list[i]), box_to_line(box_list[j])))
                total_count += 1
        if not merge_flag:
            new_box_lines.append(_box_to_line(box_list[i]))

    #print("合并了 {}个 box".format(total_count))
    #print("总共 {}个 box".format(len(new_box_lines)))
    return new_box_lines, total_count


def do_merge_box(new_lines):

    max_merge_count = 5
    for i in range(max_merge_count):
        new_lines, total_count = _do_merge_inline(new_lines)
        if total_count == 0:
            break

    return new_lines

