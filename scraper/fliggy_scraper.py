# scraper/fliggy_scraper.py

import time
import logging
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_fliggy_prices(departure_city: str, arrival_city: str, departure_date: str) -> list:
    """
    从飞猪网站抓取指定航线和日期的机票价格。
    """
    logging.info(f"开始抓取飞猪数据：{departure_city} -> {arrival_city} ({departure_date})")

    # 1. 配置浏览器选项
    edge_options = EdgeOptions()
    edge_options.add_argument("--headless") # 建议在测试时注释此行
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--window-size=1920,1080")
    edge_options.add_argument("blink-settings=imagesEnabled=false")
    edge_options.add_argument("--log-level=3")
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # 禁用自动化特征
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)


    driver = None
    try:
        # 2. 初始化WebDriver
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)

        # 注入反检测脚本
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })
        logging.info("已注入反检测脚本。")

        # 3. 访问页面
        base_url = "https://sjipiao.fliggy.com/flight_search_result.htm"
        url = f"{base_url}?tripType=0&depDate={departure_date}" # URL中只保留日期
        
        logging.info(f"正在访问URL: {url}")
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        ## ==================== 模拟用户输入（因为下拉框的存在） ==================== ##
        
        # 定义选择器变量
        dep_city_input_selector = 'input[name="depCityName"]'
        arr_city_input_selector = 'input[name="arrCityName"]'
        city_suggestion_selector = 'div.J_AcItem'
        search_button_selector = 'input.pi-btn-primary'

        # --- 操作出发城市 ---
        logging.info("操作出发城市输入框...")
        dep_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, dep_city_input_selector)))
        dep_input.click()
        time.sleep(0.5)
        dep_input.clear()
        dep_input.send_keys(departure_city)
        logging.info(f"已输入: {departure_city}")
        time.sleep(1) 
        dep_suggestion = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, city_suggestion_selector)))
        dep_suggestion.click()
        logging.info("已选择出发城市。")

        time.sleep(1)

        # --- 操作到达城市 ---
        logging.info("操作到达城市输入框...")
        arr_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, arr_city_input_selector)))
        arr_input.click()
        arr_input.send_keys(arrival_city)
        logging.info(f"已输入: {arrival_city}")
        time.sleep(1)
        
        # 获取所有建议项，并点击可见的那个
        logging.info("查找所有到达城市建议项...")
        all_suggestions = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, city_suggestion_selector)))
        
        if not all_suggestions:
            raise Exception("未能找到任何到达城市建议项。")

        logging.info(f"找到了 {len(all_suggestions)} 个建议项，正在查找可见的...")
        
        clicked = False
        for suggestion in all_suggestions:
            # is_displayed() 方法会判断元素是否在页面上可见
            if suggestion.is_displayed():
                suggestion.click()
                logging.info("已点击可见的到达城市建议项。")
                clicked = True
                break  # 点击成功后立即退出循环

        if not clicked:
            # 如果循环结束仍未点击，说明没有找到可见的选项
            raise Exception("没有找到可见的到达城市建议项可供点击。")


        # --- 点击搜索按钮 ---
        logging.info("点击搜索按钮...")
        search_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, search_button_selector)))
        search_button.click()

        ## ==================== 模拟输入结束 ==================== ##

        # 4. 等待搜索结果页面加载完成
        logging.info("等待航班列表加载...")
        flight_list_container_selector = "div.flight-list" 
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, flight_list_container_selector)))
        time.sleep(5)
        logging.info("航班列表已加载。")
    
        # 5. 查找所有航班信息卡片
        flight_item_selector = "div.flight-list-item" 
        flight_elements = driver.find_elements(By.CSS_SELECTOR, flight_item_selector)

        if not flight_elements:
            logging.warning("在页面上未找到任何航班信息。")
            return []

        logging.info(f"找到了 {len(flight_elements)} 个航班信息。开始解析...")
        
        # 6. 遍历并解析每个航班的数据
        scraped_data = []
        for flight_el in flight_elements:
            try:
                flight_number = flight_el.find_element(By.CSS_SELECTOR, "span.J_line").text 
                dep_time = flight_el.find_element(By.CSS_SELECTOR, "p.flight-time-deptime").text 
                arr_time = flight_el.find_element(By.CSS_SELECTOR, "span.s-time").text 
                price_text = flight_el.find_element(By.CSS_SELECTOR, "span.J_FlightListPrice").text 
                dep_port = flight_el.find_element(By.CSS_SELECTOR, "p.port-dep").text
                arr_port = flight_el.find_element(By.CSS_SELECTOR, "p.port-arr").text
                
                price = int("".join(filter(str.isdigit, price_text)))

                flight_data = {
                    "flight_number": flight_number.strip(),
                    "departure_time": dep_time.strip(),
                    "arrival_time": arr_time.strip(),
                    "departure_port": dep_port.strip(),
                    "arrival_port": arr_port.strip(),
                    "price": price,
                    "source_website": "Fliggy"
                }
                scraped_data.append(flight_data)

            except Exception as e:
                logging.warning(f"解析单个航班信息时出错，已跳过。错误: {e}")
                continue
        
        logging.info(f"成功解析 {len(scraped_data)} 条航班数据。")
        return scraped_data

    except Exception as e:
        error_message = f"飞猪爬虫执行失败: {e}"
        logging.error(error_message)
        raise Exception(error_message)

    finally:
        # 7. 无论成功与否，都确保关闭浏览器进程，释放资源
        if driver:
            driver.quit()
        logging.info("飞猪爬虫运行结束，浏览器已关闭。")