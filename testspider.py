import scrapy
import re
import time
from datetime import datetime


class TestSpider(scrapy.Spider):
    name = "testspider"
    allowed_domains = ["www.gov.uk"]
    start_urls = ["https://www.gov.uk/employment-tribunal-decisions"]

    custom_settings = {
        'FEED_FORMAT': 'csv',
        'FEED_URI': "test.csv"
    }

    # Collects links on page and then goes to next page
    def parse(self, response):

        # Iterate through each url and scraping the details
        urls_list = response.css('li.document > a::attr(href)').getall()
        for url in urls_list:
            url = response.urljoin(url)
            time.sleep(0.5)
            yield scrapy.Request(url=url, callback=self.parse_details, dont_filter=True)


        # Follow pagination link
        next_page = response.css('nav.gem-c-pagination > ul > li:contains("Next page") > a::attr(href)').get()
        if next_page:
            next_page = response.urljoin(next_page)
            # time.sleep(0.5)
            yield scrapy.Request(url=next_page, callback=self.parse, dont_filter=True)


    # Collect info from details page
    def parse_details(self, response):

        # Split to get Claimant, Respondent and Case ID
        full_title = response.css('h1::text').get().strip('\n": ')
        # Convert date format
        pub_date = response.css('div.app-c-published-dates::text').get().strip('\n": |Published')
        dec_date = response.css('dd.app-c-important-metadata__definition::text').get()


        yield {                       
            'claimant': re.split(' v |: |:', full_title)[0],
            'respondent': re.split(' v |: |:', full_title)[1],
            'case_id': re.split(' v |: |:', full_title)[2],
            'published_date': datetime.strptime(pub_date, '%d %B %Y').strftime('%Y-%m-%d'),
            'decision_date': datetime.strptime(dec_date, '%d %B %Y').strftime('%Y-%m-%d'),
            'country': response.css('dd.app-c-important-metadata__definition > a::text').getall()[0],
            'jurisdiction_code': response.css('dd.app-c-important-metadata__definition > a::text').getall()[1:],
            'source': response.url,
            'decision_links': response.css('span.attachment-inline > a::attr(href)').getall()
        }
