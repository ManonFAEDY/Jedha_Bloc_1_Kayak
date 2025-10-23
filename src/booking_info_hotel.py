import logging
import scrapy
from scrapy.crawler import CrawlerProcess
import json

'''
A spider that goes directly to booking.com and searches the informations for each hotel.
'''

class BookingDetailsSpider(scrapy.Spider):
    name = "booking_details"
    
    # Spider settings
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOAD_TIMEOUT': 60,
        'RETRY_TIMES': 3,
    }
    
    # Function to make requests in Booking.com by giving a hotel's URL
    def start_requests(self):
        """Loads URLs from JSON file and generates request for each hotel's URL"""

        # Load URLs from JSON file
        json_path = r'data\all_cities_urls_hotels.json'
        
        with open(json_path, 'r', encoding='utf-8') as f:
            hotels_data = json.load(f)
        
        # Log for info
        self.logger.info(f"📂 Chargement de {len(hotels_data)} URLs d'hôtels")
        
        # Generates request for each hotel's URL
        for hotel in hotels_data:
            url = hotel['url']
            city = hotel['city']
            
            yield scrapy.Request(
                url=url,
                callback=self.parse_hotel,
                meta={'city': city, 'url': url},
                errback=self.handle_error
            )
    
    def parse_hotel(self, response):
        """Extract details for each hotel's URL"""
        city = response.meta['city']
        url = response.meta['url']
        
        # Log for info
        self.logger.info(f"🏨 Extraction: {response.url}")
        
        # === HOTEL'S NAME ===
        # Multiple methodes to be sure to extract information :
        nom = response.css('h2.pp-header__title::text').get()
        if not nom:
            nom = response.css('h2[data-testid="property-name"]::text').get()
        if not nom:
            nom = response.xpath('//*[@id="hp_hotel_name"]/div/h2/text()').get()
            # nom = response.xpath('//h2[@class="hp__hotel-name"]/text()').get()
        if not nom:
            nom = response.css('h1.d2fee87262::text').get()
        
        # === Note ===
        # Multiple methodes to be sure to extract information :
        note = response.css('div.b5cd09854e::text').get()
        if not note:
            note = response.css('div[data-testid="review-score-component"] div::text').get() 
        if not note:
            note = response.xpath('//*[@id="js--hp-gallery-scorecard"]/a/div/div/div/div[2]/text()').get()

        # === COMPLETE ADRESS ===
        # Multiple methodes to be sure to extract information :
        adresse = response.css('span.hp_address_subtitle::text').get()
        if not adresse:
            adresse = response.css('span[data-node_tt_id="location_score_tooltip"]::text').get()
        if not adresse:
            adresse = response.xpath('//*[@id="wrap-hotelpage-top"]/div[3]/div/div/div/div/div/span[1]/button/div/text()').get()
        if not adresse:
            adresse = response.xpath('//*[@id="wrap-hotelpage-top"]/div[4]/div/div/div/div/div/span[1]/button/div/text()').get()
        if not adresse:
            adresse_parts = response.css('p.address span::text').getall()
            adresse = ' '.join(adresse_parts) if adresse_parts else None
        print(adresse)
        
        # === DESCRIPTION ===
        # Multiple methodes to be sure to extract information :
        description_parts = response.css('div#property_description_content p::text').getall()
        if not description_parts:
            description_parts = response.css('div.hp_desc_main_content p::text').getall()
        if not description_parts:
            description_parts = response.xpath('//*[@id="basiclayout"]/div/div[3]/div[1]/div[1]/div[1]/div[1]/div/div/p[1]/text()').getall()
        description = ' '.join(description_parts).strip() if description_parts else None
        
        # If no full description, try a shorter text
        if not description:
            description = response.css('div.a53cbfa6de::text').get()
        
        # === COMPIL RESULT ===
        hotel_data = {
            'ville': city,
            'url': url,
            'nom': nom.strip() if nom else 'Non disponible',
            'note': note.strip() if note else 'Non disponible',
            'adresse': adresse.strip() if adresse else 'Non disponible',
            'description': description if description else 'Non disponible'
        }
        
        # Log for info
        self.logger.info(f"✅ Extrait: {hotel_data['nom']} - Note: {hotel_data['note']}")
        
        yield hotel_data
    
    # Function to handle errors
    def handle_error(self, failure):
        """Handle errors"""
        self.logger.error(f"❌ Error during scrapping: {failure.value}")
        self.logger.error(f"Concerned URL : {failure.request.url}")


# === CONFIGURATION ET LAUNCH ===
if __name__ == '__main__':
    # File name to save
    output_path = r'data\hotels_details.json'
    
    # Process configuration
    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'LOG_LEVEL': logging.INFO,
        'FEEDS': {
            output_path: {
                "format": "json",
                'overwrite': True,
                'encoding': 'utf-8',
                'indent': 2
            },
        }
    })
    
    # Start scrapping
    process.crawl(BookingDetailsSpider)
    process.start()