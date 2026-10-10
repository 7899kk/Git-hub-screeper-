import { createConnector } from "../framework.mjs";
export default createConnector({"id": "amazon", "name": "Amazon India", "host": "amazon.in", "search": "/s?k=", "marker": "/dp/", "titlePattern": "id=\"productTitle\"[^>]*>([\\s\\S]*?)<", "pricePattern": "class=\"a-offscreen\"[^>]*>\\s*\u20b9([\\d,.]+)"});
