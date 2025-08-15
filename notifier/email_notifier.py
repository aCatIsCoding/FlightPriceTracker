import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import logging
import os

def send_email(subject, content, recipient, config, attachment_path=None):
    """通用的邮件发送函数"""
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = config['sender_email']
    msg['To'] = recipient
    
    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    # 添加附件
    if attachment_path:
        try:
            with open(attachment_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)
        except Exception as e:
            logging.error(f"添加附件失败: {e}")


    try:
        server = smtplib.SMTP_SSL(config['smtp_server'], int(config['port']))
        server.login(config['sender_email'], config['password'])
        server.send_message(msg)
        server.quit()
        logging.info(f"邮件已成功发送至 {recipient}")
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")

# --- 封装三种不同类型的邮件 ---

def send_price_alert(recipient, flight_info, config):
    subject = f"【重要】机票价格提醒！发现低于 ¥{flight_info['threshold']} 的机票！"
    content = f"""
    您好！

    您关注的航线出现超值低价！

    航班号: {flight_info['flight_number']}
    航线: {flight_info['dep_city']} -> {flight_info['arr_city']}
    时间: {flight_info['dep_time']} - {flight_info['arr_time']}
    当前价格: ¥{flight_info['price']}

    请尽快前往飞猪查看！
    """
    send_email(subject, content, recipient, config)

def send_error_report(recipient, error_message, config):
    subject = "【警告】FlightPriceTracker爬虫异常！"
    content = f"""
    您好！

    机票价格追踪爬虫在运行过程中发生错误。

    错误信息:
    {error_message}

    请及时登录服务器检查 `error.log` 文件并修复问题。
    """
    send_email(subject, content, recipient, config)

def send_daily_summary(recipient, analysis_result, config):
    """发送包含分析结果和图表的每日总结邮件"""
    if not analysis_result:
        logging.warning("分析结果为空，不发送每日总结。")
        return

    subject = f"每日机票价格报告 - 最低价: ¥{analysis_result['min_price']}"
    content = f"""
    您好！

    这是今日的机票价格追踪报告。

    --- 分析摘要 ---
    查询到的最低价格为: ¥{analysis_result['min_price']}
    航班信息:
      - 航班号: {analysis_result['min_price_flight']}
      - 起飞: {analysis_result['departure_time']} 从 {analysis_result['departure_port']}
      - 到达: {analysis_result['arrival_time']} 至 {analysis_result['arrival_port']}
    记录时间: {analysis_result['min_price_time']}

    详细的价格波动趋势请见附件图表。
    """
    chart_path = analysis_result.get('chart_path')
    send_email(subject, content, recipient, config, attachment_path=chart_path)