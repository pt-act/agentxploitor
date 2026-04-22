import type { NextConfig } from "next";
import path from 'path';

const nextConfig: NextConfig = {
  devIndicators: false,
  serverExternalPackages: ['@metamask/sdk', 'pino'],
  webpack: (config) => {
    // MetaMask SDK incorrectly imports react-native-async-storage in browser bundles
    config.resolve.alias = {
      ...config.resolve.alias,
      '@react-native-async-storage/async-storage': path.resolve(__dirname, 'empty-module.js'),
    };
    return config;
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' https://vercel.live",  // TODO: migrate to nonce-based CSP — Next.js requires inline scripts for hydration
              "style-src 'self' 'unsafe-inline'",  // Tailwind CSS requires unsafe-inline for styles
              "img-src 'self' data: https: blob:",
              "font-src 'self' data:",
              "connect-src 'self' https://mainnet.base.org https://api.farcaster.xyz https://*.quiknode.pro https://api.openai.com",
              "frame-ancestors https://warpcast.com https://farcaster.xyz https://*.vercel.app https://*.netlify.app",
              "base-uri 'self'",
              "form-action 'self'",
              "frame-src https://farcaster.xyz https://warpcast.com"
            ].join("; ")
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff"
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin"
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()"
          },
          {
            key: "Access-Control-Allow-Origin",
            value: "https://farcaster.xyz"
          }
        ]
      }
    ];
  }
};

export default nextConfig;