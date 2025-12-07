# -*- coding: utf-8 -*-
BOT_NAME = 'alkoteka'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 20
DOWNLOAD_DELAY = 0.5
RETRY_ENABLED = True
RETRY_TIMES = 2

DOWNLOADER_MIDDLEWARES = {
    'middlewares.RandomUserAgentMiddleware': 400,
    'middlewares.RandomProxyMiddleware': 410,
    'middlewares.DynamicDelayMiddleware': 420,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

EXTENSIONS = {
    'extensions.remove_duplicates.RemoveDuplicatesExtension': 500,
}

DOWNLOAD_TIMEOUT = 20

FEED_EXPORT_ENCODING = 'utf-8'
