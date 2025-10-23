import logging
import scrapy
from scrapy.crawler import CrawlerProcess
import pandas as pd

'''
A spider that goes directly to booking.com and searches the URL of 20 hotels for each city.
'''

# Load cities from cvs file
path_cities = r'data\cities_weather.csv'
cities_df = pd.read_csv(path_cities)

class BookingURLSpider(scrapy.Spider):
    name = "booking_urls"
    
    # Cities list
    cities = cities_df.iloc[:, 1].tolist()
    
    # Spider settings
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,  # 1 request at a time to not overload Booking.com
        'DOWNLOAD_DELAY': 5,
        'RANDOMIZE_DOWNLOAD_DELAY': True,    
        'REACTOR_THREADPOOL_MAXSIZE': 20,
    }
    
    # Function to make requests in Booking.com by giving a city name
    def start_requests(self):
        """Generates request for each city"""
        for city in self.cities:
            url = f"https://www.booking.com/searchresults.fr.html?ss={city.replace(' ', '+')}%2C+France&checkin=2025-11-03&checkout=2025-11-06&order=review_score_and_price"
            yield scrapy.Request(
                url=url, 
                callback=self.parse, 
                meta={"city": city}  # To associate URL to city name
            )
    
    # Function to get URL of each hotel on the city page
    def parse(self, response):
        """Extract URLs - ROBUST METHOD"""
        city = response.meta['city']  # Get city name

        # Multiple methodes to be sure to extract information :
        
        # - METHODE 1 : Get all links in 1 time with css path (BEST)
        hotel_links = response.css('a[data-testid="title-link"]::attr(href)').getall()
        
        # - METHODE 2 : with another css path
        if not hotel_links:
            hotel_links = response.css('h3 a::attr(href)').getall()
        
        # - METHODE 3 : with XPath
        if not hotel_links:
            hotel_links = response.xpath('//div[@data-testid="property-card"]//h3/a/@href').getall()
        
        # Log for info
        self.logger.info(f"🏙️  {city}: {len(hotel_links)} hotels found")
        
        # Limit to first 20
        for link in hotel_links[:20]:
            # Clean URL
            clean_url = link.split('?')[0] if '?' in link else link
            if clean_url.startswith('//'):
                clean_url = 'https:' + clean_url
            elif clean_url.startswith('/'):
                clean_url = 'https://www.booking.com' + clean_url
            
            # Associate city to URL
            yield {
                'city': city,
                'url': clean_url
            }

# File name to save
filenamepath = r'data\all_cities_urls_hotels.json'

# Process configuration
process_url = CrawlerProcess(settings={
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'LOG_LEVEL': logging.INFO,
    'FEEDS': {
        filenamepath: {"format": "json", 'overwrite': True},
    }
})

# Start scrapping
process_url.crawl(BookingURLSpider)
process_url.start()