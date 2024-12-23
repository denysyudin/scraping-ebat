import requests
import scrapy
from datetime import datetime
import logging

class FirstSpider(scrapy.Spider):
    name = "firstspider"
    start_urls = []
    vendors = []
    sheet_api = "https://script.google.com/macros/s/AKfycbwA1bcFfNc8lg4CsP72CetbwJRJir2Wt6wFzFYber0gwErm6qIS8u1e07DrziVnKKM/exec"
    cnt = 0
    limit = 0
    percent = 0
    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.88 Safari/537.36",
        "ROBOTSTXT_OBEY": False,  # Disable robots.txt checking
        "PROXY": None,
        "HTTP_PROXY": None,
        "HTTPS_PROXY": None
    }
        
    def start_requests(self):
        response = requests.get(self.sheet_api)
        if response.status_code == 200:
            urls = response.json()
            self.limit = len(urls['urls'])
            self.vendors.extend(urls['vendor'])
            self.start_urls.extend(urls['urls'])
            yield scrapy.Request(url=self.start_urls[self.cnt], callback=self.parse)
        else:
            logging.error(f"Failed to fetch URLs: {response.status_code}")
            return
    
    def parse(self, response):
        data = []
        itemlists = response.xpath('//div[@class="srp-river-results clearfix"]')
        print(itemlists)
        print(len(itemlists.xpath('.//div[contains(@class, "s-item__wrapper clearfix")]')))
        for item in itemlists.xpath('.//div[contains(@class, "s-item__wrapper clearfix")]'):
            try:
                sold_date = item.xpath('.//div[@class="s-item__caption--row"]//span[@class="s-item__caption--signal POSITIVE"]/span/text()').get()
                sold_date = sold_date and datetime.strptime(sold_date, "Sold %b %d, %Y").strftime("%m/%d/%Y") or "N/A"
            except Exception as e:
                logging.error(f"Sold date parsing failed: {e}")
                sold_date = "N/A"
            
            try:
                price = item.xpath('.//span[@class="s-item__price"]/span[contains(@class, "POSITIVE")]/text()').get() or "N/A"
            except Exception as e:
                logging.error(f"Price parsing failed: {e}")
                price = "N/A"

            try:
                title = item.xpath('.//div[@class="s-item__title"]//span[@role="heading"]/text()').get(default="N/A").strip()
            except Exception as e:
                logging.error(f"Title parsing failed: {e}")
                title = "N/A"

            try:
                subtitle = item.xpath('.//div[@class="s-item__subtitle"]//span[@class="SECONDARY_INFO"]/text()').get(default="N/A").strip()
            except Exception as e:
                logging.error(f"Subtitle parsing failed: {e}")
                subtitle = "N/A"

            data.append({
                "vendor": self.vendors[self.cnt],
                "solddate": sold_date,
                "price": price,
                "item": title,
                "subtitle": subtitle
            })
        # Send data to Google Sheets using `requests.post`
        self.post_to_google_sheets(data)
        
        # Handle pagination
        pagination = itemlists.xpath('.//nav[@class="pagination"]')
        next_page = pagination.xpath('.//a[contains(@class, "pagination__next")]/@href').get()
        if next_page:
            logging.info(f"Following next page: {next_page}")
            yield response.follow(next_page, self.parse)
        else:
            print("pagination", pagination)
            print("nextpage",next_page)
            self.cnt += 1
            if self.cnt <= self.limit:
                yield scrapy.Request(url=self.start_urls[self.cnt], callback=self.parse)
    
    def post_to_google_sheets(self, data):
       print("data", len(data))
       requests.post(self.sheet_api, json=data)