import scrapy
from datetime import datetime
import requests
import logging

class MySpider(scrapy.Spider):
    name = "myspider"
    start_urls = [
        'https://www.ebay.com/sch/i.html?_dkr=1&iconV2Request=true&_blrs=recall_filtering&_ssn=adamstang2005&store_cat=0&store_name=upstatewholesaleinc&_oac=1&LH_Sold=1&LH_Complete=1'
    ]
    sheet_api = "https://script.google.com/macros/s/AKfycbzYifA7_6Vs4_P3YBWwZrDV3bGfJWjCno-hCYb7-BMUIsQLjWJ6tQozlhY4HIf118c/exec"

    def parse(self, response):
        data = []
        itemlists = response.xpath('//div[@class="srp-river-results clearfix"]')
        for item in itemlists.xpath('.//div[@class="s-item__wrapper clearfix"]'):
            sold_date = item.xpath('.//div[@class="s-item__caption--row"]//span[@class="s-item__caption--signal POSITIVE"]/span/text()').get()
            try:
                if sold_date:
                    sold_date = datetime.strptime(sold_date, "Sold %b %d, %Y").strftime("%m/%d/%Y")
                else:
                    sold_date = "N/A"
            except Exception as e:
                logging.error(f"Date parsing failed: {sold_date}, error: {e}")
                sold_date = "N/A"

            price = item.xpath('.//span[@class="s-item__price"]/span[contains(@class, "POSITIVE")]/text()').get()
            title = item.xpath('.//div[@class="s-item__title"]//span[@role="heading"]/text()').get()
            
            data.append({
                "vendor": "adamstang2005",
                "soliddate": sold_date,
                "price": price,
                "item": title
            })

        if data:
            try:
                api_response = requests.post(self.sheet_api, json=data)
                api_response.raise_for_status()
                logging.info(f"Data successfully sent to API: {api_response.status_code}")
            except requests.RequestException as e:
                logging.error(f"Failed to send data to API: {e}")

        # Handle pagination
        next_page = response.xpath('//nav[@class="pagination"]//a[contains(@class, "pagination__next")]/@href').get()
        if next_page:
            next_page = response.urljoin(next_page)
        if next_page:
           logging.info(f"Following pagination link: {next_page}")
           yield scrapy.Request(url=next_page, callback=self.parse)