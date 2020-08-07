var vue ;
var table_item_index = 0
$(function(){

    vue = new Vue({
            el: '#main',
            data:{
                blockItemList:[], //当前页面解析的block元素
                tableBlockList:[],
                currentTableBlock:{},
//                data_url:"https://dikers-html.s3.cn-northwest-1.amazonaws.com.cn/ocr_output/list.json",
//                  data_url:"https://dikers-html.s3.cn-northwest-1.amazonaws.com.cn/ocr_output/test013.json",
                data_url:"https://dikers-html.s3.cn-northwest-1.amazonaws.com.cn/ocr_output/2020_05_05_pdf.json",
//                data_url:"https://dikers-html.s3.cn-northwest-1.amazonaws.com.cn/ocr_output/z003.json",
                data:{}

             },methods:{
                get_json:function(){   // 获取文件 文件保存在S3中
                    url = $("#json_url_input").val()
                    //alert(url)
                    get_data(url)
                },
                add_table_block:function(){   //添加水平表格
                    add_table_block()
                },
                add_vertical_table_block:function(){  //添加垂直表格
                    add_vertical_table_block()
                },


                create_table_split_th:function(e){    //添加水平表格分割线
                    table_block_id = e.currentTarget.name
                    create_table_split_th(table_block_id)
                },
                create_vertical_table_split_th:function(e){  //添加垂直表格分割线
                    table_block_id = e.currentTarget.name
                    create_vertical_table_split_th(table_block_id)
                },


                create_table_template:function(e){          //创建水平表格模板
                    table_block_id = e.currentTarget.name
                    create_table_template(table_block_id)
                },
                create_vertical_table_template:function(e){  //创建垂直表格模板
                    create_vertical_table_template(table_block_id)
                },


                save_template:function(){                    //保存模板
                    save_template()
                },
                delete_table_block:function(e){             // 删除表格模板
                    table_block_id = e.currentTarget.name
                    delete_table_block(table_block_id)
                }
             }
    })
    get_data(vue.data_url)
});


/**

Vue  对象的结构
--tableBlockList[]                  //一共发现多少个相同的表格模板
  --tableBlock{}
    --id                            // 【用户输入】【需要保存的内容】
    --table_name                    // 表格名称 【用户输入】【需要保存的内容】
    --main_col_num                  //主列序号   【用户输入】【需要保存的内容】
    --table_type                    // 【用户输入】【需要保存的内容】 0: 横向表格   1: 纵向表格
    --thItems[]                     //【用户输入】 模板的定位元素， 用户点击选择的Block  首位两端的就可以， 最少两个
                                    // [ {left, right, top, bottom}, {left, right, top, bottom}]
    --th_count                      //【用户输入】 【需要保存的内容】   实际表格列数， 用户自己填入， 用户生成分割线
    --row_max_height                //【用户输入】 【需要保存的内容】   用户输入的行最大的可能高度， 辅助进行识别
    --th_x_poz_list                 //【用户输入】【需要保存的内容】  用户拖动后的分割线坐标
    --save_location_items           // 【需要保存的内容】

    --status                        // 当前状态 0:新创建  1: 生成了分割线  2:生成了这个表格匹配的模板
    --col_poz_list                  // 用来分割表头元素横线的 X 坐标 集合
    --row_poz_list                  // 用来分割行元素横线的 Y 坐标 集合
*/


function get_data(url){
    if(url == null || url == ''){
        show_message(" 请填写 url ")
        return ;
    }
    vue.tableBlockList = new Array()
    vue.currentTableBlock = {}

    $("#loading-icon").show()
    $.getJSON(url, function (data) {
        parse_data(data)
        vue.data_url = url
        $("#loading-icon").hide()

    }).success(function() {

     }).error(function() {
        console.error("error");
        $("#loading-icon").hide()
            show_message("文件加载失败 请检查"+url)
        })


}

/**
新加一种类型的 tableBlock模板
*/
function add_table_block(){
    if (vue.tableBlockList.length >0 &&
            vue.currentTableBlock['status'] != undefined &&  vue.currentTableBlock['status'] !=2 ){
        show_message("请先完成前一个表格[ "+vue.currentTableBlock['id']+" ]的制作")
        return false;
    }

    var tableBlock = {}
    tableBlock['id']= uuid(8, 16)
    tableBlock['thItems'] = new Array()

    tableBlock['save_location_items'] = new Array()
    tableBlock['table_type'] = 0    //0 横向  1: 纵向
    tableBlock['table_name'] = 'tb_name_'+table_item_index
    tableBlock['th_count'] = 0                      //默认表格列数
    tableBlock['row_max_height'] = 60
    tableBlock['main_col_num'] = 1
    tableBlock['status'] = 0
    vue.currentTableBlock = tableBlock
    vue.tableBlockList.push(tableBlock)

    table_item_index += 1
}


/**
删除一个表格
1. Vue 中删除
2. UI 上删除
3. 恢复初始状态
*/
function delete_table_block(table_block_id){

    if(vue.currentTableBlock['id'] == table_block_id){
        vue.currentTableBlock = {}
    }


    vue.tableBlockList = vue.tableBlockList.filter(function(item) {
        return item['id'] != table_block_id
    });


    for(i =0 ; i<vue.blockItemList.length; i++){
        var blockItem = vue.blockItemList[i]
        if(blockItem['table_id'] == table_block_id){
            blockItem['selected'] = 0
            blockItem['blockType'] = 0 //1 表头; 2 表格中的值
            blockItem['table_id']= ''
        }
    }
    redraw_canvas()
}


/**
生成划分表格列的 分割线
*/
function create_table_split_th(table_block_id){
    if( !has_current_table_block()){
        return ;
    }

    var thItems = vue.currentTableBlock['thItems']
    if(thItems.length<2){
        show_message("定位元素最少为2个")
        return ;
    }
    if(vue.currentTableBlock['th_count']<2){
        show_message("列数最少为2个")
        return ;

    }
    var  main_col_num = vue.currentTableBlock['main_col_num'] -1
    if(main_col_num<0 || main_col_num >= vue.currentTableBlock['th_count'] ){
        show_message("主列序号设置不合理， 范围["+1+" -"+vue.currentTableBlock['th_count']+"]")
        return ;
    }

    if(vue.currentTableBlock['id'] != table_block_id){
        show_message("当前表格已经创建成功， 如需修改，请删除以后重建")
        return;
    }

    redraw_canvas()
    vue.currentTableBlock['status'] = 1
    var box = get_thItems_box(thItems)

    var row_max_height = vue.currentTableBlock['row_max_height']
    var col_num = parseInt(vue.currentTableBlock['th_count'])

    // 生成分割线， 让用户拖动， 划分单元格 x（ 水平）坐标
    create_split_thItems_line(box, col_num,  row_max_height)

}



/**
根据已经划分的表头  创建表格模板
*/
function create_table_template(table_block_id){


    if( !has_current_table_block()){
        return ;
    }
    var thItems = vue.currentTableBlock['thItems']


    if(thItems.length<2){
        show_message("定位元素最少为2个")
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

    var  main_col_num = vue.currentTableBlock['main_col_num'] -1
    if(main_col_num<0 || main_col_num >= vue.currentTableBlock['th_count'] ){
        show_message("主列序号设置不合理， 范围["+1+" -"+vue.currentTableBlock['th_count']+"]")
        return ;

    }


    vue.currentTableBlock['status'] =2
    //按照x坐标对用户选择的 定位元素进行排序
    thItems.sort(sort_block_by_x);

    //step 1.  找到表头元素，利用用户给出的分割线，列划分
    var tableItems = new Array()
    var col_poz_list = find_table_items_by_th_items(thItems)

    //step 2.  找到行划分 用户自己选按照哪一列划分行， 默认选第一列， 因为一般情况下第一列不为空
    console.log("主列数量", col_poz_list.length)
    console.log("主列： ", JSON.stringify(col_poz_list[main_col_num]))
    var row_poz_list =  find_split_row_poz_list(col_poz_list[main_col_num])

    //step 3. 利用行列 进行拆分
    vue.currentTableBlock['col_poz_list'] = col_poz_list
    vue.currentTableBlock['row_poz_list'] = row_poz_list

    if (row_poz_list.length <=0){
        show_message("没有生成表格， 请检查行高等设置！")
        redraw_canvas()
        return ;
    }

    split_td_by_col_row(vue.currentTableBlock['id'], col_poz_list, row_poz_list)

    // canvas 会通过 col_poz_list， row_poz_list 画出单元格的框线
    redraw_canvas()

}


/*
通过分割线找到表头元素
@Param old_th_items  用户选择的定位元素， 每列最好有一个定位元素， 首位的定位元素必须有
*/
function find_table_items_by_th_items(old_th_items){
    var th_x_poz_list = vue.currentTableBlock['th_x_poz_list']
    var col_poz_list = []
        //寻找在一个区间里面的表头定位元素 [left , right]
    for (var i=1; i<th_x_poz_list.length ; i++){
        var new_item = {}
        new_item['top'] = old_th_items[0]['top']
        new_item['bottom'] = old_th_items[0]['bottom']

        new_item['left'] = th_x_poz_list[i-1]
        new_item['right'] = th_x_poz_list[i]
        new_item['x'] = parseInt((new_item['left'] + new_item['right'])/ 2)
        new_item['y'] = parseInt((new_item['bottom'] + new_item['top'])/ 2)

        new_item['height'] = new_item['bottom'] - new_item['top']
        new_item['width'] = new_item['right'] - new_item['left']
        col_poz_list.push(new_item)
    }

//    for (var col_poz of col_poz_list){
//        console.error('col_poz: ', JSON.stringify(col_poz))
//    }

    return col_poz_list

}

/**
前一步已经对表头做了列的划分， 根据用户选择的列，做为划分行的参考坐标
会返回以下格式数据， 用于进行划分表格
0: {start: 268, end: 392}
1: {start: 392, end: 488}
2: {start: 488, end: 543}
3: {start: 543, end: 722}
*/
function find_split_row_poz_list(blockItem){

    //最大行高， 用来寻找行内的元素
    var row_max_height = parseInt(vue.currentTableBlock['row_max_height']) - blockItem['height']
//    var row_max_height = parseInt(vue.currentTableBlock['row_max_height'])


    var last_item_y = blockItem['bottom']
    var row_y_pos_list = new Array()
    console.log("表头最大行高 %d    last_item_y   %d", row_max_height, last_item_y)
    print_block_item('表头定位元素', blockItem)
//    console.log(" 共有元素：  ", vue.blockItemList.length)
    //遍历所有元素
    for(var i=0; i< vue.blockItemList.length; i++ ){

        var tempBlockItem = vue.blockItemList[i]
//        print_block_item("debug ---> ", vue.blockItemList[i])
        if(tempBlockItem['raw_block_type'] == "LINE"){
            continue
        }


        // 三个条件 在定位元素的下方， 左右两边在列的范围内。
        if(tempBlockItem['top'] - blockItem['bottom']> -5  &&
         tempBlockItem['left'] >= blockItem['left'] - 5  &&
         tempBlockItem['right'] <= blockItem['right'] +5){

//            console.log('find ---- [%s]  [x=%d, y=%d, left=%d, right=%d, top=%d, bottom=%d]  last_item_y= %d', tempBlockItem['text'], tempBlockItem['x'], tempBlockItem['y'],
//                                    tempBlockItem['left'], tempBlockItem['right'],tempBlockItem['top'], tempBlockItem['bottom'] , last_item_y)

            //下一个行和上一个行差距太大， 就结束查找 ， 最后一个元素作为区分表格的底部

//            console.log("^^^^^^^^^^^ ", tempBlockItem['bottom'] - last_item_y , row_max_height)
            if(tempBlockItem['bottom'] - last_item_y > row_max_height ){
//                console.log(" *找到行元素结尾 [%s]  top=%d   bottom=%d  last_item_y=%d", tempBlockItem['text'], tempBlockItem['top'], tempBlockItem['bottom'], last_item_y )
                break;
            }
            //在同一个行内的元素， y值区别不大， 直接跳过 找下一行元素
            if(tempBlockItem['bottom'] - last_item_y < tempBlockItem['bottom'] - tempBlockItem['top'] ){
//                console.log("###### ", tempBlockItem['text'], last_item_y)
                continue;
            }


            last_item_y = tempBlockItem['bottom']
            //保存上一个划分的y 坐标
            row_y_pos_list.push(tempBlockItem['top'])
        }

    }//end for


    //将 row_poz_list 封装成对象列表
    var row_poz_list = new Array()
    if(row_y_pos_list.length ==0 ){
        console.log('未找到表格元素')
    }else if(row_y_pos_list.length == 1){
        // 一个表格最大的高度， 只有一行的表格
        row_poz_list.push({'top':row_y_pos_list[0], 'bottom':row_y_pos_list[0] + row_max_height })
    }else {

        for(var i=1; i<row_y_pos_list.length; i++){
            row_poz_list.push({'top':row_y_pos_list[i-1], 'bottom':row_y_pos_list[i] })
        }
        // 最后一行的bottom = 最后一个y值 + row_max_height
        var last_y = row_y_pos_list[row_y_pos_list.length -1]
        row_poz_list.push({'top':last_y, 'bottom':last_y + row_max_height })
    }

    console.log('row_poz_list  length: %d', row_poz_list.length)

    return  row_poz_list
}


/**
根据行和列的值划分表格， 这里只打印出单元格的内容， 在flow_client 会把他们显示出来
*/

function split_td_by_col_row(table_id, col_poz_list, row_poz_list){


    for(var i=0; i<row_poz_list.length; i++ ){
        var row = row_poz_list[i]

        for(var j=0; j< col_poz_list.length; j++ ){
            var col = col_poz_list[j]

//            console.log("[left=%d,  right=%d, top=%d, bottom=%d]" ,  col['left'], col['right'] , row['top'], row['bottom']  )
            var box = {'left': col['left'], 'right': col['right'] ,
                        'top': row['top'], 'bottom': row['bottom'] }
            console.log(  "row: [%d]  col: [%d]  ----  %s", i, j, merge_td_text_by_box_poz(table_id, box) )
        }
    }
}


/**
判断是否创建了 表格模板
*/
function has_current_table_block(){

    if(vue.currentTableBlock == null || vue.currentTableBlock['id'] == null
      || vue.tableBlockList.length == 0){
        show_message(" 请先创建表格模板， 可以选择'水平' 或者'垂直' 两种形式的模板 ")
        return false;
    }
    return true
}

