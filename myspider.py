import scrapy


class ProductSpider(scrapy.Spider):
    name = 'productspider'
    start_urls =['http://perfectbody.in/new/index.php?route=product/category&path=63', ]

    def parse(self, response):
        category_names = []
        category_urls = []
        for category in response.xpath('//div[@class="list-group"]/a')[:1]:  # TODO testing with one category, remove
            category_name = category.xpath('text()').extract_first()         # TODO slicing later
            category_url = category.css('a::attr(href)').extract_first()
            print('Category: {}'.format(category_name))
            print('URL: {}'.format(category_url))
            category_names.append(category_name)
            category_urls.append(category_url)  # collecting the category urls
        # hitting the category urls, which gives a list of sub-categories
        for url in category_urls:
            request = scrapy.Request(url, callback=self.parse_sub_categories)
            yield request
        yield category_names

    def parse_sub_categories(self, response):
        # getting the list of sub-categories
        sub_categories_ul = response.xpath('//div[@id="content"]/div/div/ul').extract_first()

        selector = scrapy.selector.Selector(text=sub_categories_ul)
        sub_categories = selector.xpath('//li')
        print('Number of sub-categories: {}'.format(len(sub_categories)))
        sub_category_names = []
        sub_category_urls = []
        for sub_category in sub_categories:
            sub_category_url = sub_category.css('a::attr(href)').extract_first()
            sub_category_name = sub_category.css('a::text').extract_first()
            print('Sub category URL: {}'.format(sub_category_url))
            print('Sub category name: {}'.format(sub_category_name))
            sub_category_names.append(sub_category_name)
            sub_category_urls.append(sub_category_url)  # collecting sub-categories urls

        # hitting the sub-category urls, they contain the products so callback to parse_products
        for url in sub_category_urls:
            request = scrapy.Request(url, callback=self.parse_products)
            yield request
        yield sub_category_names

    def parse_products(self, response):
        # reaching to the div which contains all the products on the page
        products_div = response.xpath('//div[@id="content"]/div')[1]
        # getting all the divs which contain one product each
        product_divs = products_div.xpath('.//div[contains(@class,"product-layout")]')
        # their length will obviously give number of products on the page
        print('Number of products: ', len(product_divs))
        # import ipdb; ipdb.set_trace()
        # iterating over each product div to get product data
        products_data = []
        for product_div in product_divs:
            product_dict = {}
            image_url = product_div.xpath('.//div[@class="image"]/a/img').css('img::attr(src)').extract_first()
            title = product_div.xpath('.//div[@class="caption"]/h4').css('a::text').extract_first()
            price_new = product_div.xpath(
                './/div[@class="caption"]/p/span[@class="price-new"]'
            ).css('span::text').extract_first()
            price_old = product_div.xpath(
                './/div[@class="caption"]/p/span[@class="price-old"]'
            ).css('span::text').extract_first()
            product_dict['title'] = title
            product_dict['price_new'] = price_new
            product_dict['price_old'] = price_old
            product_dict['image'] = image_url
            print('Product data:')
            print('Title: ', title)
            print('Price new: ', price_new)
            print('Price old: ', price_old)
            print('Image: ', image_url)

            products_data.append(product_dict)
        # handling pagination
        pagination_items = response.xpath('//ul[@class="pagination"]/li')
        next_url = None
        # check if next page exists
        for item in pagination_items:
            page = item.css('a::text').extract_first()
            if page and page == '>':  # `>` is the symbol for next page
                next_url = item.css('a::attr(href)').extract_first()
                print('Next URL: ', next_url)
                break
        if next_url:
            yield response.follow(next_url, self.parse_products)
        yield products_data
