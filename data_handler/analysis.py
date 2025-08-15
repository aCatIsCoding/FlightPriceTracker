import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import logging
from datetime import datetime

def analyze_and_visualize(csv_path: str) -> dict:
    """
    分析航班价格数据，生成可视化图表，并返回分析摘要。

    Args:
        csv_path (str): CSV数据文件的路径。

    Returns:
        dict: 一个包含分析结果的字典，例如：
              {
                  'min_price': 850,
                  'min_price_flight': '深航ZH9876',
                  'min_price_time': '2025-07-13 05:00:00',
                  'chart_path': 'price_trend_analysis.png'
              }
              如果数据不足或出错，则返回None。
    """
    try:
        logging.info("开始执行数据分析与可视化...")
        df = pd.read_csv(csv_path)

        # 1. 数据预处理
        # 确保数据量足够进行分析
        if len(df) < 2:
            logging.warning("数据量不足，无法生成趋势图。")
            return None
        
        # 将时间戳字符串转换为datetime对象，便于按时间排序和绘图
        df['scrape_timestamp'] = pd.to_datetime(df['scrape_timestamp'])
        df = df.sort_values('scrape_timestamp')

        # 2. 寻找最低价
        min_price_row = df.loc[df['price'].idxmin()]
        analysis_summary = {
            'min_price': min_price_row['price'],
            'min_price_flight': min_price_row['flight_number'],
            'min_price_time': min_price_row['scrape_timestamp'].strftime('%Y-%m-%d %H:%M'),
            'departure_time': min_price_row['departure_time'], 
            'arrival_time': min_price_row['arrival_time'],     
            'departure_port': min_price_row['departure_port'], 
            'arrival_port': min_price_row['arrival_port'],     
            'chart_path': 'price_trend_analysis.png'
        }
        logging.info(f"分析完成：最低价格为 ¥{analysis_summary['min_price']}，航班 {analysis_summary['min_price_flight']}.")

        # 3. 数据可视化折线图
        
        plt.rcParams['font.sans-serif'] = ['SimHei'] 
        plt.rcParams['axes.unicode_minus'] = False 
        plt.figure(figsize=(16, 9)) 
        for flight_number, group in df.groupby('flight_number'):
            plt.plot(group['scrape_timestamp'], group['price'], marker='o', linestyle='-', label=flight_number)
        plt.title(f'机票价格变化趋势分析 ({df["scrape_timestamp"].min().date()} - {df["scrape_timestamp"].max().date()})', fontsize=20)
        plt.xlabel('抓取时间', fontsize=14)
        plt.ylabel('价格 (¥)', fontsize=14)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend(title='航班号', bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.gcf().autofmt_xdate()
        plt.savefig(analysis_summary['chart_path'], dpi=300, bbox_inches='tight')
        plt.close() 
        logging.info(f"价格趋势图已保存至 {analysis_summary['chart_path']}")

        return analysis_summary

    except Exception as e:
        logging.error(f"数据分析时发生错误: {e}")
        return None