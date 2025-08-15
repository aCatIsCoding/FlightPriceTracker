# ✈️ Flight Price Tracker - 机票价格追踪器

一个没什么水平的Python爬虫插件，可以爬取指定网站的指定航班价格，并发送消息到你的邮箱。

自由度还行，可以同时抓取同日同航线的全部航班，也可锁定单一航班，无需频繁修改配置文件。

## 核心功能

- **定时抓取**: 每小时自动从飞猪抓取指定航线的航班价格。
- **数据存储**: 将抓取到的数据以CSV格式持久化存储。
- **低价提醒**: 当发现机票价格低于预设阈值时，立即发送邮件提醒。
- **异常监控**: 当爬虫程序运行出错时，发送错误报告邮件。
- **每日报告**: 每天定时生成价格趋势图，并以邮件形式发送分析摘要。

## 安装与配置

1.  **克隆仓库**
    
2.  **安装依赖**
    
    ```bash
    pip install -r requirements.txt
    ```
    
4.  **配置程序**
    
    - 复制配置文件模板
    - 打开 `config.ini` 文件，按需填入你的信息。

## 使用方法

**1. 长期后台监控 (使用config.ini中的默认配置)**

```bash
python main.py
```

**2.  执行一次性查询**

```bash
# 查询指定日期的价格，并只运行一次
python main.py --date 2025-12-25 --run_once

# 临时查询不同航线和价格阈值
python main.py --dep_city 北京 --arr_city 广州 --threshold 1200 --run_once
```

**3. 查看所有可用参数**

```bash
python main.py --help
```

## 项目结构

```
FlightPriceTracker/
├── .gitignore          
├── config.example.ini  
├── main.py             
├── notifier/           
├── scraper/            
├── data_handler/       
├── requirements.txt    
└── README.md           
```

## 可能增加的新功能（大概率不会（

| 其他网站支持（例如携程、去哪儿） |  -   |
| :------------------------------: | :--: |
|   **同目录下同时执行多个爬虫**   |  -   |
|       **转机、往返等监控**       |  -   |
|      **日报、周报甚至月报**      |  -   |



## 许可证

本项目采用 [MIT License](LICENSE) 开源。