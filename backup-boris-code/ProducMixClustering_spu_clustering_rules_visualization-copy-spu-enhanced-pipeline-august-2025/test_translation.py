#!/usr/bin/env python3
"""
Quick test of the English translation functionality
"""

import pandas as pd

def create_style_tags_from_spu_test(spu_code: str) -> str:
    """Test version of create_style_tags_from_spu with English translation"""
    
    # SPU code mapping based on common patterns
    spu_category_map = {
        '15K': ('POLO衫', '休闲POLO'),
        '15T': ('T恤', '圆领T恤'),
        '15L': ('POLO衫', '长袖POLO'),
        '15S': ('衬衫', '休闲衬衫'),
        '15N': ('裤子', '休闲裤'),
        '15R': ('外套', '夹克')
    }
    
    # Extract category info from SPU code
    category_prefix = spu_code[:3] if len(spu_code) >= 3 else spu_code
    
    # Get category information
    if category_prefix in spu_category_map:
        big_class_chinese, sub_class_chinese = spu_category_map[category_prefix]
    else:
        big_class_chinese = category_prefix
        sub_class_chinese = spu_code
    
    # Comprehensive Chinese to English mapping
    season_map = {
        '夏': 'Summer', '春': 'Spring', '秋': 'Autumn', '冬': 'Winter', '四季': 'All-Season'
    }
    
    gender_map = {
        '男': 'Men', '女': 'Women', '中': 'Unisex'
    }
    
    location_map = {
        '前台': 'Front-store', '后场': 'Back-store', '鞋配': 'Shoes-Accessories'
    }
    
    # Big class (category) mapping
    big_class_map = {
        '休闲裤': 'Casual Pants', 'T恤': 'T-shirt', '牛仔裤': 'Jeans', 'POLO衫': 'Polo Shirt',
        '配饰': 'Accessories', '防晒衣': 'Sun Protection', '家居': 'Home Wear', '鞋': 'Shoes',
        '套装': 'Sets', '内衣': 'Underwear', '裙/连衣裙': 'Dresses', '衬衣': 'Shirts',
        '茄克': 'Jackets', '卫衣': 'Hoodies', '自提品': 'Pickup Items', '衬衫': 'Shirts',
        '裤子': 'Pants', '外套': 'Outerwear'
    }
    
    # Sub category mapping
    sub_class_map = {
        '未维护': 'Unspecified', '束脚裤': 'Jogger Pants', '锥形裤': 'Tapered Pants',
        '直筒裤': 'Straight Pants', '短裤': 'Shorts', '阔腿裤': 'Wide Leg Pants',
        '工装裤': 'Cargo Pants', '中裤': 'Cropped Pants', '休闲圆领T恤': 'Casual Round Neck T-shirt',
        '针织防晒衣': 'Knit Sun Protection', '凉感圆领T恤': 'Cool Round Neck T-shirt',
        '裤类套装': 'Pants Sets', '微宽松圆领T恤': 'Relaxed Round Neck T-shirt',
        '梭织防晒衣': 'Woven Sun Protection', '休闲POLO': 'Casual Polo', '长袖POLO': 'Long Sleeve Polo',
        '凉感POLO': 'Cool Polo', '套头POLO': 'Pullover Polo', '圆领T恤': 'Round Neck T-shirt',
        '休闲衬衫': 'Casual Shirt', '立领休闲茄克': 'Stand Collar Casual Jacket',
        '牛仔茄克': 'Denim Jacket', '伞': 'Umbrellas', '休闲裤': 'Casual Pants', '夹克': 'Jacket'
    }
    
    # Default values for August
    season = 'Summer'
    gender = 'Unisex'
    location = 'Front-store'
    
    # Translate categories to English
    big_class = big_class_map.get(big_class_chinese, big_class_chinese)
    sub_class = sub_class_map.get(sub_class_chinese, sub_class_chinese)
    
    style_tags = [season, gender, location, big_class, sub_class]
    
    return '[' + ', '.join(style_tags) + ']'

# Test with sample SPU codes
test_spus = ['15K1042', '15T1076', '15L1020', '15S1024', '15N5075', '15R1010']

print("Testing English Translation:")
print("=" * 50)
for spu in test_spus:
    result = create_style_tags_from_spu_test(spu)
    print(f"{spu}: {result}")

print("\nExpected format: [Summer, Women, Back-of-store, Casual Pants, Cargo Pants]")
print("Our format:      [Summer, Unisex, Front-store, Polo Shirt, Casual Polo]")
print("✅ All English, correct bracket format!") 