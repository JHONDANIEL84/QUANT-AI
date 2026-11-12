/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_APP_NAME: "QUANT AI",
    NEXT_PUBLIC_DEFAULT_CURRENCY: "COP",
    NEXT_PUBLIC_DEFAULT_TIMEZONE: "America/Bogota",
  },
};

export default nextConfig;
