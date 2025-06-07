"""
gzh公众号 scraping functionality.
"""

import requests
import time
import datetime
import logging
from typing import List, Dict
from urllib.parse import quote_plus

from business_validator.config import GZH_AUTH_TOKEN 

def scrape_gzh(keyword: str, page: int = 0) -> dict:
     
    # URL encode the keyword to handle spaces and special characters
    encoded_keyword = quote_plus(keyword)
    template = 'https://api.tikhub.io/api/v1/wechat_mp/web/fetch_mp_article_list?ghid={}&page={}'
    notes = []
    note_ids = set()
    current_page = 1
    headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {GZH_AUTH_TOKEN}'
        }
    print(headers)
    while current_page <= 3:
        url = template.format(encoded_keyword, current_page)
        try:
            logging.info(f"请求URL：{url}")
            response = requests.get(url, headers=headers )
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 200:
                logging.error(f"API请求失败，状态码：{data.get('code')}，信息：{data.get('message')}")
                break

            items = data.get("data", {}).get("list", [])
            for item in items:
                note = parse_gzh(item,keyword)
                if note['note_id'] and note['note_id'] not in note_ids:
                    note_ids.add(note['note_id'])
                    notes.append(note)

            # 根据新API调整分页判断（假设返回字段为has_next_page）
            if not data.get("data", {}).get("has_next_page", False):
                break
            current_page += 1
            sleep(1)
        except Exception as e:
            logging.error(f"爬取失败，公众号ID：{keyword}，错误：{e}")
            return {'posts': []}
            break

    return {'posts': notes}    

    
    

def parse_gzh(item, ghid) :
 
    return {
            'note_id': item.get("comment_topic_id"),  # 使用评论主题ID作为唯一标识
            'title': item.get("Title"),
            'digest': item.get("Digest"),  # 新增摘要字段
            'user_nickname':  ghid,  # 固定为公众号来源
            'content_url': item.get("ContentUrl"),  # 文章链接
            'source_url': item.get("SourceUrl"),  # 原文链接
            'cover_url': item.get("CoverImgUrl"),
            'publish_time': datetime.datetime.fromtimestamp(item.get("send_time", 0)).strftime("%Y-%m-%d %H:%M:%S"),  # 时间戳转字符串
            'is_original': bool(item.get("IsOriginal", 0)),  # 是否原创（整数转布尔）
            'synced': False,
        
        }
    
