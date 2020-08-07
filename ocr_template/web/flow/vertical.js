/*
在页面上添加垂直表格
*/
function add_vertical_table_block(){

    //判断表格处理的状态
    if (vue.tableBlockList.length >0 && vue.currentTableBlock['status'] !=2 ){
        show_message("请先完成前一个表格[ "+vue.currentTableBlock['id']+" ]的制作")
        return false;
    }

    var tableBlock = {}
    tableBlock['id']= uuid(8, 16)
    tableBlock['thItems'] = new Array()             // 定位元素

    tableBlock['save_location_items'] = new Array()
    tableBlock['table_type'] = 1                    //0 水平  1: 垂直
    tableBlock['table_name'] = 'tb_name_'+table_item_index
    tableBlock['th_count'] = 0                      //默认表格列数
    tableBlock['row_max_height'] = 40               //最后一行的高度
    tableBlock['status'] = 0                        //当前操作状态
    vue.currentTableBlock = tableBlock
    vue.tableBlockList.push(tableBlock)             //将当前模板加入到列表中

    table_item_index += 1                           //表格模板索引加1 ， 用户最好用自己的业务数据进行替换


}

/*
在页面上画出分割线
*/
function create_vertical_table_split_th(table_block_id){

    // 当前没有创建表格模板
    if( !has_current_table_block()){
        return ;
    }
    //
    var thItems = vue.currentTableBlock['thItems']
    if(thItems.length<1){C
        show_message("至少一个定位元素")
        return ;
    }

    // 已经创建好的表格， 不能修改， 只能删除， 如果要做成表格可以编辑， 需要在表格点击的时候切换Current Table block
    if(vue.currentTableBlock['id'] != table_block_id){
        show_message("当前表格已经创建成功， 如需修改，请删除以后重建")
        return;
    }

    // 当前状态设置为
    vue.currentTableBlock['status'] = 1

    var box = get_thItems_box(thItems, vue.currentTableBlock['th_count'])  //生成表头整个区域

    var row_max_height = parseInt(vue.currentTableBlock['row_max_height']) // 最后一行的高度
    if (row_max_height< 15 || row_max_height> 500){  // 设置行高过大过小， 需要确认是否输入错误，后期可以修改这两个值
        show_message("请确认行高是否正确 ")
        return;
    }
    redraw_canvas() //重新绘制整个区域， 生成分割线
    create_split_thItems_line(box, 1,  row_max_height)


}

/**
创建表格模板
*/
function create_vertical_table_template(table_block_id){
    if( !has_current_table_block()){
        return ;
    }
    var thItems = vue.currentTableBlock['thItems']  //定位元素

    if(thItems.length<1){
        show_message("至少有一个定位元素")
        return ;
    }
    if( vue.currentTableBlock['status'] != 1){
        show_message("请先生成分割线")
        return;
    }
     if(vue.currentTableBlock['id'] != table_block_id){
        show_message("当前表格已经创建成功， 如需修改，请删除以后重建")
        return;
    }

    if(vue.currentTableBlock['table_name'] == ''){
        show_message("请填写表格名称")
        return ;
    }
    // 用户手动拖动的分割线横坐标位置， 保存在下面的数组中
    var th_x_poz_list = vue.currentTableBlock['th_x_poz_list']

    console.log('th_x_poz_list: ', th_x_poz_list)
    // 垂直表格， 只有左右两个边界， 将他们做成一个对方，放入到列表中
    var col_poz = {'left':th_x_poz_list[0], 'right': th_x_poz_list[1]}
    var col_poz_list = []
    col_poz_list.push(col_poz)


    // 状态修改为创建完成状态
    vue.currentTableBlock['status'] =2


    //step 1. 找到每行第一个元素， 找到行的划分
    var tableItems = new Array()
    var row_poz_list = find_first_block_in_line(thItems)

    vue.currentTableBlock['row_poz_list'] = row_poz_list         // 行的分割线
    vue.currentTableBlock['col_poz_list'] = col_poz_list         // 列的分割线
    split_vertical_td_by_col_row(thItems, row_poz_list, col_poz_list)   // 划分单行格
    redraw_canvas()


}

/**
找到划分行的y 坐标
把所有元素 按照y排序， 每行取一个元素
*/
function  find_first_block_in_line(thItems){
    var line_error_rate = 15         //
    thItems.sort(sort_block_by_y);  // 按照y 坐标进行排序

    var new_item_poz_list = []
    new_item_poz_list.push(thItems[0]['top'])
    for(var i=1; i<thItems.length; i++){
        // 垂直表格 划分行元素，每一个元素和最后一个元素y坐标比较， 如果差距大于15 ， 就认为已经换行了， 从下一行计算
        if( Math.abs(thItems[i]['top'] - new_item_poz_list[new_item_poz_list.length-1]) > line_error_rate ){
            new_item_poz_list.push(thItems[i]['top'])
        }
    }

    // 然后把最后一行的最大高度加到最后， 就完成了所有的行的划分
    new_item_poz_list.push(new_item_poz_list[new_item_poz_list.length-1] +
                    parseInt(vue.currentTableBlock['row_max_height']))
    console.log("new_th_item_list: ", JSON.stringify(new_item_poz_list ))

    //将y坐标封装成对象， 包含top 和bottom， 数量会比队列减少1
    var row_poz_list = []
    for(var j=1; j< new_item_poz_list.length; j++ ){
        var row_poz = {'top':new_item_poz_list[j-1], 'bottom':new_item_poz_list[j]}
        row_poz_list.push(row_poz)
    }

//    console.error("row_poz_list: ", JSON.stringify(row_poz_list ))
    return row_poz_list
}

/**
划分行内元素,根据分割线做成小区域， 然后在每个小区域里面找到对应的元素。
*/
function split_vertical_td_by_col_row(thItems, row_poz_list, col_poz_list){


    //col_poz_list[0]  左右位置已经固定， 列划分里面只有一个元素， 包括了最左边和最右边的分割线
    //然后循环行元素
    var blockItemList = vue.blockItemList

    var table_row_list = [] // {'key': key , 'value': value}


    for (var row of row_poz_list){
        var box = {'left': col_poz_list[0]['left'], 'right': col_poz_list[0]['right'] ,
                     'top': row['top'], 'bottom': row['bottom'] }

        var find_row_block_list = find_block_list_in_box(box)
    }




}
/**
在指定的区域内， 找到对应的元素
*/
function find_block_list_in_box(box){
//   console.log("box  ", JSON.stringify(box))
   var block_list = []
   for(var blockItem of vue.blockItemList){
        if (blockItem['raw_block_type'] =='LINE'){
            continue
        }
        if ( blockItem['x'] > box['left'] && blockItem['x']<= box['right']
           &&  blockItem['y']> box['top'] && blockItem['y'] <= box['bottom']){
            block_list.push(blockItem)
//            console.log("***********   ", blockItem['text'])

        }
   }

    return block_list
}