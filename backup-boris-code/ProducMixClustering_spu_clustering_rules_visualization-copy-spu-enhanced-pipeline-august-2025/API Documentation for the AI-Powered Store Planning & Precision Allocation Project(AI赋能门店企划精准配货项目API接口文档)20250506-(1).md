  
**1:门店销售接口**

**接口地址** https://fdapidb.fastfish.com:8089/api/sale/getAdsAiStrSal

**请求方式** POST

**请求类型** \["application/json"\]

**请求参数 json（示例）**  
{  
"strCodes": \[  
"51274"  
\],  
"yyyymm": "202505"  
}

**参数说明**

| 参数名称 | 说明 | 是否必须 | 类型   |
| :---- | :---- | :---- | :---- |
| strCodes | 门店编码,最大100 | true | array |
| yyyymm | 年月格式:yyyymm | true | string |

**响应示例 json**

`{`  
    `"code": 1,`  
    `"data": [`  
        `{`  
      `"avg_temp": 26.293487179487176,`  
      `"base_sal_amt": 10396.500000000002,`  
      `"base_sal_qty": 143,`  
      `"display_type": "M",`  
      `"distrib_name": "西南",`  
      `"fashion_sal_amt": 13905.800000000003,`  
      `"fashion_sal_qty": 158,`  
      `"go_by_str_cnt_avg": 5011,`  
      `"into_str_cnt_avg": 302,`  
      `"long_lat": "110.854,21.9178",`  
      `"male_into_str_cnt_avg": 109,`  
      `"max_temp": 35.99,`  
      `"min_temp": 14.99,`  
      `"mm": "5",`  
      `"mm_type": "5A",`  
      `"sal_type": "C",`  
      `"str_code": "51274",`  
      `"str_format": "街边店",`  
      `"str_name": "雷波店",`  
      `"str_type": "流行",`  
      `"temp_zone": "西南",`  
      `"woman_into_str_cnt_avg": 192,`  
      `"yyyy": "2025"`  
    `}`  
    `],`  
    `"message": "成功"`  
`}`

**响应参数**

| 参数名称 | 说明 | 类型   |
| :---- | :---- | :---- |
| code | 返回码：1成功，-1失败 | int32 |
| data | 数据 | array |
| message | 返回信息描述 | string |

**data字段说明**

| 属性名称 | 说明 | 类型 | schema   |
| :---- | :---- | :---- | :---- |
| yyyy | 年份 | string |  |
| mm | 月份 | string |  |
| mm\_type | 月类型 | string |  |
| str\_code | 门店编码 | string |  |
| str\_name | 门店名称 | string |  |
| distrib\_name | 分区名称 | string |  |
| long\_lat | 经纬度 | string |  |
| temp\_zone | 温度带 | string |  |
| str\_type | 店铺类型 | string |  |
| str\_format | 业态分类 | string |  |
| sal\_type | 销售分类 | string |  |
| display\_type | 高架陈列面分类 | string |  |
| avg\_temp | 平均气温 | double |  |
| max\_temp | 最高气温 | double |  |
| min\_temp | 最低气温 | double |  |
| base\_sal\_amt | 基础销售金额 | double |  |
| base\_sal\_qty | 基础销售数量 | double |  |
| fashion\_sal\_amt | 流行销售金额 | double |  |
| fashion\_sal\_qty | 流行销售数量 | double |  |
| go\_by\_str\_cnt\_avg | 平均过店客流 | double |  |
| into\_str\_cnt\_avg | 平均进店客流 | double |  |
| male\_into\_str\_cnt\_avg | 平均男进店客流 | double |  |
| woman\_into\_str\_cnt\_avg | 平均女进店客流 | double |  |

**2:门店配置接口**

**接口地址** https://fdapidb.fastfish.com:8089/api/sale/getAdsAiStrCfg

**请求方式** POST

**请求类型** \["application/json"\]

**请求参数 json（示例）**  
{  
"strCodes": \[  
"51274"  
\],  
"yyyymm": "202505"  
}

**参数说明**

| 参数名称 | 说明 | 是否必须 | 类型   |
| :---- | :---- | :---- | :---- |
| strCodes | 门店编码,最大100 | true | array |
| yyyymm | 年月格式:yyyymm | true | string |

**响应示例 json**

`{`  
    `"code": 1,`  
    `"data": [`  
       `{`  
      `"big_class_name": "卫衣",`  
      `"display_location_name": "后场",`  
      `"ext_sty_cnt_avg": 1,`  
      `"ext_sty_cnt_end": 1,`  
      `"ext_sty_detail": "14W5108",`  
      `"mm": "5",`  
      `"mm_type": "5A",`  
      `"season_name": "秋",`  
      `"sex_name": "女",`  
      `"str_code": "51274",`  
      `"str_name": "雷波店",`  
      `"sub_cate_name": "翻领卫衣",`  
      `"target_sty_cnt_avg": 0,`  
      `"target_sty_cnt_end": 0,`  
      `"yyyy": "2025"`  
    `}`  
    `],`  
    `"message": "成功"`  
`}`

**响应参数**

| 参数名称 | 说明 | 类型   |
| :---- | :---- | :---- |
| code | 返回码：1成功，-1失败 | int32 |
| data | 数据 | array |
| message | 返回信息描述 | string |

**data字段说明**

| 属性名称 | 说明 | 类型   |
| :---- | :---- | :---- |
| yyyy | 年份 | string |
| mm | 月份 | string |
| mm\_type | 月类型 | string |
| str\_code | 门店编码 | string |
| str\_name | 门店名称 | string |
| season\_name | 季节 | string |
| sex\_name | 性别 | string |
| display\_location\_name | 陈列位置 | string |
| big\_class\_name | 大类 | string |
| sub\_cate\_name | 小类 | string |
| target\_sty\_cnt\_avg | 目标款数平均 | double |
| ext\_sty\_cnt\_avg | 现有款数平均 | double |
| target\_sty\_cnt\_end | 目标款数期末 | double |
| ext\_sty\_cnt\_end | 现有款数期末 | double |
| ext\_sty\_detail | 现有款拼接 | string |

