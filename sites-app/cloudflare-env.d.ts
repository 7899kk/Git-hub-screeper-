declare namespace Cloudflare {
  interface Env {
    DB?: D1Database;
    OWNER_PASSWORD?: string;
    REQUIRE_OWNER_AUTH?: string;
    BUCKET?: R2Bucket;
  }
}
