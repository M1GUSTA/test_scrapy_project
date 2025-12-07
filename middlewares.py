import random


class RandomProxyMiddleware:
    def __init__(self, proxies):
        self.proxies = proxies or []

    @classmethod
    def from_crawler(cls, crawler):
        proxies = []
        try:
            with open('proxies.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    p = line.strip()
                    if p:
                        proxies.append(p)
        except FileNotFoundError:
            env_proxy = crawler.settings.get('PROXY')
            if env_proxy:
                proxies.append(env_proxy)
        return cls(proxies)

    def process_request(self, request, spider):
        if not self.proxies:
            return
        proxy = random.choice(self.proxies)
        # ожидаемые форматы: http://ip:port или http://user:pass@ip:port
        request.meta['proxy'] = proxy


class RandomUserAgentMiddleware:
    def __init__(self, uas):
        self.uas = uas or []

    @classmethod
    def from_crawler(cls, crawler):
        uas = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        ]
        return cls(uas)

    def process_request(self, request, spider):
        ua = random.choice(self.uas)
        request.headers.setdefault('User-Agent', ua)


class DynamicDelayMiddleware:
    def process_request(self, request, spider):
        if 'proxy' in request.meta:
            request.meta['download_delay'] = random.uniform(0.05, 0.15)
        else:
            request.meta['download_delay'] = 0.5