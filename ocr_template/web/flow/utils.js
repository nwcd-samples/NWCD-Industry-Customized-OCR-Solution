/**
根据ID找到元素
*/
function find_block_by_id(block_id){

   for(var i=0; i< vue.blockItemList.length; i++  ){
        if (block_id ==vue.blockItemList[i]['id'] ){
            return vue.blockItemList[i]
        }
   }
}


/**
根据 坐标  找到word 元素, 并且合并文本内容,
并且将这些元素拆分
*/
function merge_td_text_by_box_poz(table_id, box){

   var td_text = ''
   for(var blockItem of vue.blockItemList){
        if (blockItem['raw_block_type'] =='LINE'){
            continue
        }
        if ( blockItem['x'] > box['left'] && blockItem['x']<= box['right']
           &&  blockItem['y']> box['top'] && blockItem['y'] <= box['bottom']){
            td_text +=  ' '+ blockItem['text']

        }
   }
   return td_text
}


/**
重新调整canvas 的大小
*/
function reset_canvas(width, height){
    var canvas=document.getElementById("myCanvas");
    canvas.width=width
    canvas.height=height

}


/**
找到最宽的元素， 用它来进行页面的旋转
*/
function find_max_width_block(blockList){
        var max_width_block = null
        max_width = 0.0
        for(i =0 ; i< blockList.length; i++){
               width =  blockList[i]['Geometry']['BoundingBox']['Width']
               if(width> max_width){
                max_width = width
                max_width_block = blockList[i]
               }
        }
        return max_width_block;
}


/**
找到每一页空白的地方， 去除掉， 防止有偏移
**/
function init_page_margin_block(blockItemList){
        var min_top_block = null
        var page_top = 1
        var page_bottom = 0.0
        var page_left = 1
        var page_right = 0.0

        for(i =0 ; i< blockItemList.length; i++){
               var top =  blockItemList[i]['newPoly'][0]['y']
               if(top<page_top){
                    page_top = top
               }
               var left =  blockItemList[i]['newPoly'][0]['x']
               if(left<page_left){
                  page_left = left
               }

               var bottom =  blockItemList[i]['newPoly'][2]['y']
               if(bottom > page_bottom){
                   page_bottom = bottom
               }

               var right =  blockItemList[i]['newPoly'][2]['x']
               if(right > page_right){
                   page_right = right
               }

        }


        var page_margin ={'top':0, 'bottom':1, 'left':0, 'right':'1'}
        page_margin['top'] = page_top;
        page_margin['bottom'] = page_bottom;
        page_margin['left'] = page_left;
        page_margin['right'] = page_right;
        page_margin['height'] = page_bottom - page_top;


        page_margin['height_rate'] = 1.0/(page_bottom - page_top);
        page_margin['width_rate'] =  1.0/(page_right - page_left)  ;

//        console.log("page_margin",  JSON.stringify(page_margin))
        return page_margin;

}

/**
把现有元素等比例放大， 占满空间
*/
function zoom_layout_block(blockItem, document_zoom_out_height){

    var polyArray  = blockItem['newPoly']
    for (var i=0; i<polyArray.length; i++){
        var poly = polyArray[i];
        poly['x'] = parseInt(poly['x']  * page_width)
        poly['y'] = parseInt(poly['y']  * page_height)
    }
    blockItem['width'] = parseInt(polyArray[1]['x'] - polyArray[0]['x'])
    blockItem['height'] = parseInt(polyArray[3]['y'] - polyArray[0]['y'])
    blockItem['left'] = polyArray[0]['x']
    blockItem['top'] = polyArray[0]['y']
    blockItem['right'] = polyArray[1]['x']
    blockItem['bottom'] = polyArray[2]['y']
    blockItem['x'] = parseInt((polyArray[2]['x'] + polyArray[0]['x']) / 2.0)
    blockItem['y'] = parseInt((polyArray[2]['y'] + polyArray[0]['y']) / 2.0)
}

/**
获取一个表头几个元素总区域的坐标位置， top  left  right  height
用于画分割线
*/
function  get_thItems_box(thItems, th_count){

    if(thItems.length <1){
        show_message(" 至少选择一个定位元素 ")
        return ;
    }

    var max_top = 100000;
    var max_left = 100000;
    var max_right = 0;
    var max_bottom = 0;

    for (var i =0; i< thItems.length; i++ ){
        if(thItems[i]['top'] < max_top){
            max_top = thItems[i]['top']
        }

        if(thItems[i]['left'] < max_left){
            max_left = thItems[i]['left']
        }

        if(thItems[i]['right'] > max_right){
            max_right = thItems[i]['right']
        }

        if(thItems[i]['bottom'] > max_bottom){
            max_bottom = thItems[i]['bottom']
        }

    }

    var box = {
        th_count: th_count,
        top: max_top -1,
        left: max_left -2,
        right: max_right + 1,
        bottom: max_bottom + 2
    }
    console.log("get_thItems_box: ", JSON.stringify(box))
    return box
}

/**
显示错误消息
*/
function show_message(message){
    $("#myModalContent").html(message)
    $('#myModal').modal('show')
}

/**
对表格分割线的X 坐标进行排序， 并且返回list
*/
function sort_map_return_list(data_map){
    var dataArray= []
    for (var item of data_map ){
        dataArray.push(item[1])
    }
    dataArray = dataArray.sort(function(a,b){return a-b})

    console.log('sort map : ', JSON.stringify(dataArray))
    return dataArray;
}

/**
保存定位元素
*/
function copy_block_item(block_item){

    var new_block_item = {}
    new_block_item['left'] = block_item['left']
    new_block_item['id'] = block_item['id']
    new_block_item['right'] = block_item['right']
    new_block_item['top'] = block_item['top']
    new_block_item['bottom'] = block_item['bottom']
    new_block_item['text'] = block_item['text']

    return new_block_item
}

/**
保存模板
*/
function save_template(){


    if(vue.tableBlockList ==null || vue.tableBlockList.length ==0 ){
        show_message("尚未创建任何表格")
        return ;
    }


    var template_name = $("#template_name_id").val()

    if(template_name == null || template_name.length<=0){
        show_message("请添加模板名称")
        $("#template_name_id").focus()
        return ;
    }


    var save_table_block_list = new Array()
    for (var  tableBlock of vue.tableBlockList){
        var table_block_item = {}
        if(tableBlock['status'] != 2){
            continue
        }
        //需要保存的元素
        table_block_item['th_count'] =  tableBlock['th_count']                          // 列数
        table_block_item['row_max_height'] =  tableBlock['row_max_height']              // 最大行高
        table_block_item['save_location_items'] =  tableBlock['save_location_items']    // 定位元素列表
        table_block_item['table_name'] =  tableBlock['table_name']                      // 表格名称
        table_block_item['table_type'] =  tableBlock['table_type']                      // 表格类型
        table_block_item['main_col_num'] =  tableBlock['main_col_num']                  // 主列编号
        table_block_item['th_x_poz_list'] =  tableBlock['th_x_poz_list']                // 分割线

        save_table_block_list.push(table_block_item)

    }

    localStorage.setItem(template_name, JSON.stringify(save_table_block_list));

//    save_template_str = localStorage.getItem(template_name)
//    var obj = JSON.parse(save_template_str);


    var  template_list = localStorage.getItem(LOCAL_SAVE_NAME_TEMPLATE_LIST)

    if (template_list == null || template_list == ""){
        template_list = new Array()
    }else {
        template_list = JSON.parse(template_list);
    }

    var isFindFlag = false

    for (var  _save_template_name of template_list){
        if(_save_template_name == template_name){
            isFindFlag = true
        }
    }
    //将模板保存到模板列表中
    if(isFindFlag == false){
        template_list.push(template_name)
        localStorage.setItem(LOCAL_SAVE_NAME_TEMPLATE_LIST, JSON.stringify(template_list));
    }

    show_message("模板 ["+template_name+"] 创建成功。 ")

}





/**
将页面元素添加到 表格中， 作为表格定位元素
*/
function add_block_to_current_table(blockItem){

//    console.log("blockItem id: ", blockItem['id'])
    if( !has_current_table_block()){
            return false;
    }
    if (vue.currentTableBlock['status'] !=0 ){
        show_message("已经选取完元素， 如果希望重新选择， 请点击删除")
        return false;
    }

    var thItems = vue.currentTableBlock['thItems']
    blockItem['blockType']= 1 // 0 未选中 1 表头; 2 表格中的值
    blockItem['table_id']= vue.currentTableBlock['id']
    thItems.push(blockItem)

    var save_location_items = copy_block_item(blockItem)
    vue.currentTableBlock['save_location_items'].push(save_location_items)

    vue.currentTableBlock['thItems'] =  thItems
    return true;
}

/**
将页面元素从表格中删除
*/
function remove_block_from_current_table(blockItem){

//    console.log("blockItem id: ", blockItem['id'])
    if( !has_current_table_block()){
            return false;
    }
    if (vue.currentTableBlock['status'] !=0 ){
        show_message("已经选取完元素， 如果希望重新选择， 请点击删除")
        return false;
    }

    var thItems = vue.currentTableBlock['thItems']

    var delete_index = -1;
    for(var i=0; i<thItems.length; i++){
        if(thItems[i]['id'] == blockItem['id']){
            blockItem['table_id']= ''
            blockItem['blockType'] = 0
            delete_index = i

        }
    }
    thItems.splice(delete_index, delete_index+1)
    var save_location_items = copy_block_item(blockItem)
    vue.currentTableBlock['save_location_items'].push(save_location_items)
    vue.currentTableBlock['thItems'] =  thItems
    return true;
}


