
/**
找到col_poz_list
垂直表格， 只有左右两个范围
*/
function find_table_items_by_th_items_vertical(thItems, th_x_poz_list){

    var col_poz = {'left':th_x_poz_list[0], 'right': th_x_poz_list[1]}
    var col_poz_list = []
    col_poz_list.push(col_poz)
    return col_poz_list
}


/***
//step 2.  找到行划分 row_poz_list
*/
function find_split_row_poz_list_vertical(thItems, row_max_height){

    var line_error_rate = 15
    thItems.sort(sort_block_by_y);

    var new_item_poz_list = []
    new_item_poz_list.push(thItems[0]['top'])
    for(var i=1; i<thItems.length; i++){

        if( Math.abs(thItems[i]['top'] - new_item_poz_list[new_item_poz_list.length-1]) > line_error_rate ){
            new_item_poz_list.push(thItems[i]['top'])
        }
    }

    new_item_poz_list.push(new_item_poz_list[new_item_poz_list.length-1] +
                    parseInt(row_max_height))
    console.log("new_th_item_list: ", JSON.stringify(new_item_poz_list ))


    var row_poz_list = []
    for(var j=1; j< new_item_poz_list.length; j++ ){
        var row_poz = {'top':new_item_poz_list[j-1], 'bottom':new_item_poz_list[j]}
        row_poz_list.push(row_poz)
    }

    console.log("row_poz_list: ", JSON.stringify(row_poz_list ))
    return row_poz_list
}

/*
* 找出表格元素
*/
function split_td_by_col_row_vertical(col_poz_list, row_poz_list){

      var table_row_list = []
        for(var i=0; i<row_poz_list.length; i++ ){
            var row = row_poz_list[i]

            var col = col_poz_list[0]
            console.log("[left=%d,  right=%d, top=%d, bottom=%d]" ,  col['left'], col['right'] , row['top'], row['bottom']  )
            var box = {'left': col['left'], 'right': col['right'] ,
                        'top': row['top'], 'bottom': row['bottom'] }

            var td_text_list = merge_td_text_by_box_block_type(box)

            table_row_list.push(td_text_list)
        }

        return table_row_list

}


/**
根据 坐标  找到word 元素, 并且合并文本内容,
并且将这些元素拆分
*/
function merge_td_text_by_box_block_type(box){


   var td_text_th = ''   // 定位元素
   var td_text = ''      // 普通元素
   for(var blockItem of vue.blockItemList){
        if (blockItem['raw_block_type'] =='LINE'){
            continue
        }
        if ( blockItem['x'] > box['left'] && blockItem['x']<= box['right']
           &&  blockItem['y']> box['top'] && blockItem['y'] <= box['bottom']){

            if(blockItem['blockType'] == 0){
                td_text +=  ' '+ blockItem['text']
            }else {
                td_text_th += ' '+ blockItem['text']
            }

        }
   }
   var td_text_list = []
    td_text_list.push(td_text_th)
    td_text_list.push(td_text)

   return td_text_list
}


/**
根据定位元素， 寻找thItem
*/
function find_th_items_from_location_item_vertical(save_location_items, th_x_poz_list){

        var total_th_item_list = []
        var error_range = 50  // 左右误差范围
        save_location_items.sort(sort_block_by_y);



        var first_item = save_location_items[0]

        var first_item_list = []
        //找到符合要求的所有第一个元素， 然后按照第一个元素继续寻找
        for(var i=0; i<vue.blockItemList.length; i++ ){
            if (vue.blockItemList[i]['raw_block_type'] =='LINE'){
                continue
            }

            var _blockItem = vue.blockItemList[i]
            if(_blockItem['text'] == first_item['text']
                 && _blockItem['x'] > first_item['left'] - error_range
                 && _blockItem['x'] < first_item['right'] + error_range
                 ){
                 first_item_list.push(_blockItem)

             }
        }

        var top  = save_location_items[0]['top']
        var bottom = save_location_items[save_location_items.length-1]['bottom']


        //在一个页面中， 可以找到多个符合要求的表格
        for(var first_item of first_item_list){

            print_block_item('first_item    ',  first_item)
            var th_item_list = find_target_block_item_list(first_item, save_location_items)
            if(th_item_list != null){
                total_th_item_list.push(th_item_list)
            }
        }

        return total_th_item_list


}

/*
找到第一定位元素以后， 做坐标偏移， 然后依次找出偏移以后的新元素，
如果都找到了， 就找到了表格， 如果有没有找到的元素， 就说明这个定位元素没有找到指定表格。

实际使用中要主要页面x坐标的误差范围，
*/
function find_target_block_item_list(first_item, save_location_items){


    var target_block_item_list = []
    target_block_item_list.push(first_item)
    print_block_item('first block ' , first_item)
    print_block_item('save  block ' , save_location_items[0])
    var del_x = first_item['left'] - save_location_items[0]['left']
    var del_y = first_item['top'] - save_location_items[0]['top']

//    console.log("###### del_x:%d   del_y: %d", del_x, del_y)

    for(var i=1; i<save_location_items.length; i++ ){

        var target_blockItem = {}
        // 根据第一个元素的坐标， 移动自己的坐标， 然后在页面里面进行寻找
        target_blockItem['top'] = save_location_items[i]['top'] + del_y
        target_blockItem['bottom'] = save_location_items[i]['bottom'] + del_y

        target_blockItem['left'] = save_location_items[i]['left'] + del_x
        target_blockItem['right'] = save_location_items[i]['right'] + del_x
        target_blockItem['text'] = save_location_items[i]['text']
        target_blockItem['id'] = save_location_items[i]['id']

        var new_block_item =  find_block_item_in_box(target_blockItem)

        if(new_block_item == null){
            return null
        }
        target_block_item_list.push(new_block_item)
    }

    if(target_block_item_list.length == save_location_items.length){
        for (var targetItem of target_block_item_list){
            targetItem['blockType'] = 1
        }

        return target_block_item_list
    }

    return null
}

/*
在指定范围里面寻找一个 blockItem
*/

function find_block_item_in_box(target_blockItem){

    var error_range = 10
    for(var _blockItem of  vue.blockItemList){
        if (_blockItem['raw_block_type'] =='LINE'){
            continue
        }

        if(_blockItem['text'] == target_blockItem['text']
            && _blockItem['x'] > target_blockItem['left'] - error_range
            && _blockItem['x'] < target_blockItem['right'] + error_range
            && _blockItem['y'] > target_blockItem['top'] - error_range
            && _blockItem['y'] < target_blockItem['bottom'] + error_range){

            return _blockItem
        }
    }
    return null;
}