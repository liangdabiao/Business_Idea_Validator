"""
xhs公众号 scraping functionality.
"""

import requests
import time
import datetime
import logging
from typing import List, Dict
from urllib.parse import quote_plus

from business_validator.config import XHZ_AUTH_TOKEN 

def scrape_xhs_search(keyword: str, page: int = 0) -> dict:
     
    # URL encode the keyword to handle spaces and special characters
    #encoded_keyword = quote_plus(keyword)
    # 确保keyword是字符串
    encoded_keyword = quote_plus(keyword)
    template = 'https://api.tikhub.io/api/v1/xiaohongshu/web/search_notes?keyword={}&page={}&sort=general&noteType=_0'
    notes = []
    note_ids = set()
    current_page = 1
    headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {XHZ_AUTH_TOKEN}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    print(headers)
    while current_page <= page:
        url = template.format(encoded_keyword, current_page)
        print(url)
        try:
            logging.info(f"请求URL：{url}")
            response = requests.get(url, headers=headers )
            response.raise_for_status()
            data = response.json()
            print(data)
            if data.get("code") != 200:
                logging.error(f"API请求失败，状态码：{data.get('code')}，信息：{data.get('message')}")
                break
            print(30)
            items = data.get("data", {}).get("data", {}).get("items", [])
            for item in items:
                note = parse_xhs(item.get("note", {}),keyword)
                if note['note_id'] and note['note_id'] not in note_ids:
                    note_ids.add(note['note_id'])
                    notes.append(note)

            print(31)
            # 根据新API调整分页判断（假设返回字段为has_next_page）
            if not data.get("data", {}).get("has_next_page", False):
                break
            current_page += 1
            print(32)
            time.sleep(1)  # 修正为time.sleep
        except Exception as e:
            logging.error(f"爬取失败，xhs搜索关键词：{keyword}，错误：{e}")
            return {'posts': []}
    print(33)
    return {'posts': notes}    

    
    

def parse_xhs(item, keyword) :
 
    return {
            'note_id': item.get("id"),  # 使用评论主题ID作为唯一标识
            'title': item.get("title"),
            'desc': item.get("desc"),  # 新增摘要字段
            'user_nickname':  item.get("user", {}).get('nickname'),   
            'publish_time': item.get("timestamp"),
            'liked_count':item.get("liked_count"),
            'collected_count':item.get("collected_count"),
            'shared_count':item.get("shared_count"),
            'comments_count':item.get("comments_count"),
            'keyword': keyword,
            'synced': False,
        
        }
    





def scrape_xhs_post_comments(post_url: str) -> List[dict]:
    """Scrape comments from a specific xhs post.
    
    Args:
        post_url: The URL of the xhs post
        
    Returns:
        List of dictionaries containing comment information
    """
    # ScraperAPI payload for individual xhs post - updated based on working example
    note_id  =  post_url 
    template = 'https://api.tikhub.io/api/v1/xiaohongshu/web/get_note_comments?note_id={}'
    notes = []
    note_ids = set()
    current_page = 1
    headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {XHZ_AUTH_TOKEN}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    print("scrape_xhs_post_comments:") 
    url = template.format(note_id)
    try:
            logging.info(f"请求URL：{url}")
            response = requests.get(url, headers=headers )
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 200:
                logging.error(f"API请求失败，状态码：{data.get('code')}，信息：{data.get('message')}")
                return {'posts': []}
             
            items = data.get("data", {}).get("data", {}).get("comments", [])
            for item in items:
                print(item)
                note = parse_xhs_comments(item,note_id)
                if note['id'] and note['id'] not in note_ids:
                    note_ids.add(note['id'])
                    notes.append(note)
   
    except Exception as e:
            logging.error(f"爬取失败，xhs搜索关键词：{keyword}，错误：{e}")
            return {'posts': []}

    return notes   
 



def parse_xhs_comments(item: str ,note_id) -> List[dict]:
    return {
            'id': item.get("id"),  # 使用评论主题ID作为唯一标识
            'note_id': note_id,  # 使用评论主题ID作为唯一标识 
            'content': item.get("content"),  # 新增摘要字段
            'user':  item.get("user", {}).get('nickname'),   
            'time': item.get("time"),
            'ip_location':item.get("ip_location"),   
        }
