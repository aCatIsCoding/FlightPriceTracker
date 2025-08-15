import pandas as pd
import os
import logging
from datetime import datetime

def save_to_csv(data_list: list, file_path: str):
    """
    将包含航班数据的列表追加到CSV文件中。
    如果文件不存在，则创建并写入表头。
    """
    if not data_list:
        logging.warning("传入的数据为空，不执行存储操作。")
        return

    # 为每条数据增加一个抓取时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for row in data_list:
        row['scrape_timestamp'] = timestamp

    df = pd.DataFrame(data_list)
    
    # 检查文件是否存在，以决定是否需要写入表头
    file_exists = os.path.exists(file_path)
    
    try:
        df.to_csv(file_path, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
        logging.info(f"已成功将 {len(data_list)} 条数据保存至 {file_path}")
    except Exception as e:
        logging.error(f"数据保存失败: {e}")