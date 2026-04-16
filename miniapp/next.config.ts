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
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://vercel.live",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https: blob:",
              "font-src 'self' data:",
              "connect-src 'self' https://mainnet.base.org https://api.farcaster.xyz",
              "frame-ancestors *",
              "base-uri 'self'",
              "form-action 'self'",
              "frame-src https://farcaster.xyz"
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