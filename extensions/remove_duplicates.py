import json
from scrapy import signals


class RemoveDuplicatesExtension:
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_closed,
                                signal=signals.spider_closed)
        return ext

    def spider_closed(self, spider):
        fname = spider.settings.get('FEED_URI')
        if not fname:
            return

        print(f"Removing duplicates in {fname}...")

        with open(fname, "r", encoding="utf-8") as f:
            data = json.load(f)

        seen = set()
        cleaned = []

        for item in data:
            key = item.get("RPC") or item.get("url")
            if key and key not in seen:
                cleaned.append(item)
                seen.add(key)

        with open(fname, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)

        print(f"Duplicates removed: {len(data) - len(cleaned)}")
