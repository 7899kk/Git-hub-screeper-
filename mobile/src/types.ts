export type Match = {
  status: "exact" | "likely" | "similar" | "unverified";
  reason: string;
};
export type Listing = {
  id: string;
  retailer: string;
  retailer_name: string;
  title: string;
  url: string;
  brand: string;
  model: string;
  gtin: string;
  variant: Record<string, string>;
  condition: string;
  price: number;
  shipping: number | null;
  currency: string;
  seller: string | null;
  availability: string;
  timestamp: string;
  source: string;
  offers: string[];
  match: Match;
  stale: boolean;
  age_hours: number;
  affiliate: boolean;
  image?: string | null;
};
export type Point = { timestamp: string; price: number; source: string };
export type History = {
  points: Point[];
  statistics: {
    count: number;
    minimum: number | null;
    maximum: number | null;
    average: number | null;
    median: number | null;
  };
  message: string;
};
export type Retailer = {
  id: string;
  name: string;
  domains: string[];
  status: string;
  message: string;
  affiliate: string;
  capabilities: string[];
};
export type Alert = {
  id: number;
  listing: Listing;
  target: number;
  triggered: boolean;
};
export type Resolution = {
  status: string;
  message?: string;
  listing?: Listing;
  canonical_url: string;
  domain?: string;
  job_id?: string;
};
