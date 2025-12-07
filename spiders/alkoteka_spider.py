import time
import scrapy


DEFAULT_REGION = {
    "name": "Краснодар",
    "id": "4a70f9e0-46ae-11e7-83ff-00155d026416"
}


class AlkotekaSpider(scrapy.Spider):
    name = "alkoteka"

    custom_settings = {
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def start_requests(self):
        with open("categories.txt", "r", encoding="utf-8") as f:
            categories = [x.strip() for x in f if x.strip()]

        for url in categories:
            slug = url.rstrip("/").split("/")[-1]
            api_url = (
                "https://alkoteka.com/web-api/v1/product"
                f"?city_uuid={DEFAULT_REGION['id']}"
                f"&page=1"
                f"&per_page=50"
                f"&root_category_slug={slug}"
            )
            yield scrapy.Request(
                api_url,
                callback=self.parse_category_api,
                cb_kwargs={"slug": slug, "page": 1}
            )

    def parse_category_api(self, response, slug, page):
        data = response.json()
        products = data.get("results", [])

        for p in products:
            product_url = p["product_url"]
            product_slug = p["slug"]
            api_product = (
                f"https://alkoteka.com/web-api/v1/product/{product_slug}"
                f"?city_uuid={DEFAULT_REGION['id']}"
            )

            yield scrapy.Request(
                api_product,
                callback=self.parse_product,
                cb_kwargs={"url": product_url}
            )

        meta = data.get("meta", {})
        if meta.get("has_more_pages"):
            print("Next page:", page + 1)
            next_page = page + 1
            next_url = (
                "https://alkoteka.com/web-api/v1/product"
                f"?city_uuid={DEFAULT_REGION['id']}"
                f"&page={next_page}"
                f"&per_page=50"
                f"&root_category_slug={slug}"
            )
            yield scrapy.Request(
                next_url,
                callback=self.parse_category_api,
                cb_kwargs={"slug": slug, "page": next_page}
            )

    def parse_product(self, response, url):
        data = response.json().get("results", {})

        title = data.get("name", "")

        volume = self.extract_volume(data)
        if volume and volume not in title:
            title = f"{title}, {volume}"

        brand = self.extract_brand(data)

        section = self.extract_categories(data)

        marketing = []
        if data.get("price_details"):
            marketing.extend([x.get("title") for x in data["price_details"] if x.get("title")])

        original = data.get("prev_price") or data.get("price")
        current = data.get("price")

        sale_tag = ""
        if original and current and current < original:
            discount = round((original - current) / original * 100)
            sale_tag = f"Скидка {discount}%"

        qty = data.get("quantity_total") or 0
        main_image = data.get("image_url", "")

        gallery = []
        if data.get("gallery"):
            gallery = data["gallery"]
        else:
            if main_image:
                gallery = [main_image]

        view360 = []
        if data.get("panorama"):
            view360 = data["panorama"] if isinstance(data["panorama"], list) else [data["panorama"]]

        video = []
        if data.get("video"):
            video = data["video"] if isinstance(data["video"], list) else [data["video"]]

        metadata = {}

        description_text = ""
        for block in data.get("text_blocks", []):
            if block.get("title") == "Описание":
                description_text = block.get("content", "").replace("<br>", "\n").replace("<br/>", "\n")

        metadata["__description"] = description_text

        for block in data.get("description_blocks", []):
            key = block.get("title")
            if not key:
                continue
            val = self.extract_block_value(block)
            if val is not None:
                metadata[key] = val

        for fl in data.get("filter_labels", []):
            key = fl.get("title")
            if key and key not in metadata:
                if fl.get("type") == "range":
                    mn = fl.get("values", {}).get("min")
                    mx = fl.get("values", {}).get("max")
                    metadata[key] = f"{mn}-{mx}" if mn and mx else ""
                else:
                    metadata[key] = fl.get("title")

        variants = len(data.get("child_products") or [])

        item = {
            "timestamp": int(time.time()),
            "RPC": str(data.get("vendor_code", "")),
            "url": url,
            "title": title,
            "marketing_tags": marketing,
            "brand": brand,
            "section": section,

            "price_data": {
                "current": float(current) if current else 0.0,
                "original": float(original) if original else 0.0,
                "sale_tag": sale_tag
            },

            "stock": {
                "in_stock": qty > 0,
                "count": qty
            },

            "assets": {
                "main_image": main_image or "",
                "set_images": gallery,
                "view360": view360,
                "video": video
            },

            "metadata": metadata,
            "variants": variants
        }

        yield item

    def extract_volume(self, data):
        for block in data.get("description_blocks", []):
            if block.get("code") == "obem":
                mn = block.get("min")
                mx = block.get("max")
                unit = block.get("unit", "").strip()
                if mn == mx:
                    return f"{mn}{unit}"
                return f"{mn}-{mx}{unit}"
        return None

    def extract_brand(self, data):
        for block in data.get("description_blocks", []):
            if block.get("code") == "brend":
                vals = block.get("values")
                if vals:
                    return vals[0].get("name")
        return None

    def extract_categories(self, data):
        cat = data.get("category")
        if not cat:
            return []
        parent = cat.get("parent", {}).get("name")
        current = cat.get("name")
        return [c for c in [parent, current] if c]

    def extract_block_value(self, block):
        if block["type"] == "select":
            return ", ".join([v["name"] for v in block.get("values", [])])

        if block["type"] == "range":
            mn = block.get("min")
            mx = block.get("max")
            unit = block.get("unit", "")
            if mn == mx:
                return f"{mn}{unit}"
            return f"{mn}-{mx}{unit}"

        return None
