import configparser
import logging
import schedule
import time
import argparse  
from scraper.fliggy_scraper import get_fliggy_prices
from data_handler.storage import save_to_csv
from data_handler.analysis import analyze_and_visualize 
from notifier.email_notifier import send_price_alert, send_error_report, send_daily_summary

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("error.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- 主工作函数 (现在接收参数) ---
def scrape_job(args): # 函数接收解析后的参数
    logging.info("--- 开始执行抓取任务 ---")
    
    # 1. 读取配置文件作为默认值
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    # 命令行参数覆盖配置文件
    # 如果命令行传入了值(not None)，则使用命令行参数；否则，使用配置文件中的值。
    dep_city = args.dep_city if args.dep_city else config['Flight']['departure_city']
    arr_city = args.arr_city if args.arr_city else config['Flight']['arrival_city']
    dep_date = args.date if args.date else config['Flight']['departure_date']
    threshold = args.threshold if args.threshold is not None else int(config['Flight']['price_threshold'])
    target_flight_no = args.flight_no if args.flight_no else None 

    logging.info(f"当前任务参数: {dep_city} -> {arr_city}, 日期: {dep_date}, 低价阈值: ¥{threshold}")
    if target_flight_no:
        logging.info(f"已锁定航班: {target_flight_no}")

    email_config = config['Email']
    alerts_config = config['Alerts']
    csv_file_path = 'data/flight_prices.csv'
    
    # 3. 调用爬虫
    try:
        flight_data = get_fliggy_prices(
            departure_city=dep_city,
            arrival_city=arr_city,
            departure_date=dep_date
        )
        
        if flight_data:
            # 如果锁定了航班号，在这里进行筛选
            if target_flight_no:
                flight_data = [f for f in flight_data if target_flight_no in f['flight_number']]
                logging.info(f"筛选后，找到 {len(flight_data)} 条匹配航班 {target_flight_no} 的数据。")

            save_to_csv(flight_data, csv_file_path)
            
            # 价格阈值判断
            for flight in flight_data:
                if flight['price'] < threshold:
                    logging.info(f"发现低价机票！价格: ¥{flight['price']}, 低于阈值 ¥{threshold}")
                    alert_info = {
                        'threshold': threshold,
                        'flight_number': flight['flight_number'],
                        'dep_city': dep_city,
                        'arr_city': arr_city,
                        'dep_time': flight['departure_time'],
                        'arr_time': flight['arrival_time'],
                        'price': flight['price']
                    }
                    send_price_alert(alerts_config['recipient_email'], alert_info, email_config)
        else:
            logging.warning("爬虫未返回任何数据。")
            
    except Exception as e:
        logging.error(f"任务执行过程中发生严重错误: {e}", exc_info=True)
        send_error_report(alerts_config['recipient_email'], str(e), email_config)
        
    logging.info("--- 抓取任务执行完毕 ---")

def daily_report_job():
    logging.info("--- 开始执行每日分析报告任务 ---")
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    email_config = config['Email']
    alerts_config = config['Alerts']
    csv_file_path = 'data/flight_prices.csv'

    # 1. 调用分析模块
    analysis_result = analyze_and_visualize(csv_file_path)

    # 2. 如果分析成功，发送邮件报告
    if analysis_result:
        send_daily_summary(alerts_config['recipient_email'], analysis_result, email_config)

    logging.info("--- 每日分析报告任务执行完毕 ---")
    
# --- 主程序入口 ---
def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="机票价格追踪器。命令行参数会覆盖config.ini中的设置。")
    parser.add_argument('--dep_city', type=str, help='出发城市 (例如: 北京)')
    parser.add_argument('--arr_city', type=str, help='到达城市 (例如: 上海)')
    parser.add_argument('--date', type=str, help='出发日期 (格式: YYYY-MM-DD)')
    parser.add_argument('--threshold', type=int, help='价格提醒阈值 (例如: 800)')
    parser.add_argument('--flight_no', type=str, help='(可选) 要锁定的特定航班号，之后将只爬取这一航班。（例如：CA1234）')
    parser.add_argument('--run_once', action='store_true', help='(可选) 只执行一次任务，不进入定时循环')
    
    args = parser.parse_args()

    # 如果设置了 run_once，则只执行一次
    if args.run_once:
        scrape_job(args)
        # 单独测试报告功能，正常使用时请注释以下两行
        # if args.report_only:
            # daily_report_job()
        return

    # 否则，进入定时调度模式
    logging.info("程序启动，进入定时调度模式。")
    # 将args传递给定时任务
    schedule.every().hour.at(":01").do(scrape_job, args=args)
    # 每天早上9点执行一次分析报告任务
    schedule.every().day.at("09:00").do(daily_report_job)
    
    logging.info("所有定时任务已设置。")
    # 为了快速测试，可以取消下面这行注释来立即执行一次报告
    # daily_report_job()
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()