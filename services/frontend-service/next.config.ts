import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',
  
  // Environment configuration
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  
  // API configuration for backend services
  async rewrites() {
    return [
      {
        source: '/api/auth/:path*',
        destination: `${process.env.AUTH_SERVICE_URL || 'http://localhost:8001'}/api/v1/auth/:path*`,
      },
      {
        source: '/api/creators/:path*',
        destination: `${process.env.CREATOR_HUB_SERVICE_URL || 'http://localhost:8002'}/api/v1/creators/:path*`,
      },
      {
        source: '/api/ai/:path*',
        destination: `${process.env.AI_ENGINE_SERVICE_URL || 'http://localhost:8003'}/api/v1/:path*`,
      },
    ];
  },
  
  // Disable experimental features for Turbopack compatibility
  // experimental: {
  //   typedRoutes: true,
  // },
};

export default nextConfig;
