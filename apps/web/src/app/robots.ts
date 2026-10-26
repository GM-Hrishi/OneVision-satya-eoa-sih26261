import type { MetadataRoute } from "next";

// Internal tool: nothing is to be indexed.
export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: "*", disallow: "/" } };
}
