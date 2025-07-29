#!/usr/bin/env python3
"""
单个Notebook文件翻译脚本
使用DeepSeek API翻译指定的notebook文件
"""

import os
import json
import re
import requests
import time

# DeepSeek API配置
DEEPSEEK_API_KEY = ""
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

def is_english_content(text):
    """检查文本是否主要是英文内容"""
    if not text.strip():
        return False
        
    # 去掉代码块、HTML标签等
    clean_text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    clean_text = re.sub(r'<[^>]+>', '', clean_text)
    clean_text = re.sub(r'`[^`]+`', '', clean_text)
    clean_text = re.sub(r'\[.*?\]\(.*?\)', '', clean_text)
    
    # 检查是否包含英文单词
    english_words = re.findall(r'\b[a-zA-Z]+\b', clean_text)
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', clean_text)
    
    # 如果英文单词数量超过3个且中文字符少于英文字符，认为是英文内容
    if len(english_words) >= 3 and len(chinese_chars) < len(''.join(english_words)) * 0.5:
        return True
    return False

def translate_text(text):
    """使用DeepSeek API翻译文本"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的技术文档翻译助手。请将用户提供的英文内容翻译成中文，保持Markdown格式不变，保留所有的代码块、链接、HTML标签等。翻译要准确、自然，符合中文表达习惯。对于专业术语，可以在首次出现时保留英文原文并加上中文翻译。"
                },
                {
                    "role": "user",
                    "content": f"请将以下内容翻译成中文，保持格式不变：\n\n{text}"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(
            DEEPSEEK_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result['choices'][0]['message']['content']
            return translated_text
        else:
            print(f"API请求失败: {response.status_code} - {response.text}")
            return text
            
    except Exception as e:
        print(f"翻译失败: {str(e)}")
        return text

def translate_notebook(file_path):
    """翻译指定的notebook文件"""
    print(f"正在处理文件: {file_path}")
    
    try:
        # 读取notebook文件
        with open(file_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        translated_count = 0
        
        # 处理所有单元格
        if 'cells' in notebook:
            for i, cell in enumerate(notebook['cells']):
                if cell.get('cell_type') == 'markdown' and 'source' in cell:
                    source = cell['source']
                    
                    # 处理不同格式的source
                    if isinstance(source, list):
                        original_text = ''.join(source)
                    else:
                        original_text = source
                    
                    if is_english_content(original_text):
                        print(f"\n单元格 {i+1}: 翻译内容...")
                        print(f"原文: {original_text[:100]}...")
                        
                        translated_text = translate_text(original_text)
                        
                        # 更新单元格内容
                        if isinstance(source, list):
                            cell['source'] = [translated_text]
                        else:
                            cell['source'] = translated_text
                        
                        print(f"译文: {translated_text[:100]}...")
                        translated_count += 1
                        
                        # 添加延迟避免API频率限制
                        time.sleep(2)
        
        if translated_count > 0:
            # 创建备份
            # backup_path = file_path + '.backup'
            # if not os.path.exists(backup_path):
            #     import shutil
            #     shutil.copy2(file_path, backup_path)
            #     print(f"已创建备份文件: {backup_path}")
            
            # 保存翻译后的文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ 翻译完成! 共翻译了 {translated_count} 个单元格")
        else:
            print("\n- 未找到需要翻译的英文内容")
            
    except Exception as e:
        print(f"处理文件失败: {str(e)}")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python translate_single.py <notebook_file_path>")
        print("示例: python translate_single.py './01_Getting_&_Knowing_Your_Data/World Food Facts/Exercises.ipynb'")
        return
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    if not file_path.endswith('.ipynb'):
        print("请提供一个 .ipynb 文件")
        return
    
    translate_notebook(file_path)

if __name__ == "__main__":
    main()
