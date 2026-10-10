import { createConnector } from "../framework.mjs";
export default createConnector({"id": "snapdeal", "name": "Snapdeal", "host": "snapdeal.com", "search": "/search?keyword=", "marker": "/product/", "titlePattern": "class=\"pdp-e-i-head\"[^>]*>(.*?)<", "pricePattern": "itemprop=\"price\"[^>]*content=\"([\\d.]+)\""});
