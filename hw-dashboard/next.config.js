/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "noriel.ro" },
      { protocol: "https", hostname: "*.noriel.ro" },
      { protocol: "https", hostname: "smyk.ro" },
      { protocol: "https", hostname: "*.smyk.ro" },
      { protocol: "https", hostname: "*.media.noriel.ro" },
    ],
  },
};

module.exports = nextConfig;
