import type { NextConfig } from "next";

// Security headers configuration
const securityHeaders = [
  {
    key: "X-DNS-Prefetch-Control",
    value: "on",
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  {
    key: "X-XSS-Protection",
    value: "1; mode=block",
  },
  {
    key: "X-Frame-Options",
    value: "SAMEORIGIN",
  },
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "Permissions-Policy",
    value: "camera=(self), microphone=(self), geolocation=(self), interest-cohort=()",
  },
  {
    key: "Content-Security-Policy",
    value: [
      // Default to self
      "default-src 'self'",
      // Scripts: self, inline for Next.js, and specific CDNs
      [
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
        process.env.NODE_ENV !== "production" ? "'unsafe-eval'" : "",
        "https://js.stripe.com https://apis.google.com https://*.firebaseapp.com",
      ].filter(Boolean).join(" "),
      // Worker/WebAssembly
      "worker-src 'self' blob:",
      "child-src 'self' blob:",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      // Images: self and allowed image hosts
      "img-src 'self' data: blob: https://res.cloudinary.com https://placehold.co https://i.postimg.cc https://*.googleusercontent.com https://*.google.com https://firebasestorage.googleapis.com https://*.youtube.com https://img.youtube.com",
      // Fonts: self and Google Fonts
      "font-src 'self' https://fonts.gstatic.com",
      // Connect: API endpoints (localhost for dev)
      "connect-src 'self' http://localhost:* http://127.0.0.1:* https://*.firebaseio.com https://*.googleapis.com https://accounts.google.com https://oauth2.googleapis.com https://api.stripe.com wss://*.firebaseio.com https://firestore.googleapis.com https://*.firebaseapp.com https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://api.deepseek.com https://ark.cn-beijing.volces.com https://2capi.com https://*.tcloudbase.com https://*.tencentcs.com https://*.cloudbasescn.com",
      // Frame ancestors: prevent clickjacking
      "frame-ancestors 'self'",
      // Form actions
      "form-action 'self'",
      // Frames: Stripe and Firebase auth iframes, YouTube
      "frame-src 'self' https://js.stripe.com https://hooks.stripe.com https://*.firebaseapp.com https://accounts.google.com https://apis.google.com https://www.youtube.com https://youtube.com",
      // Base URI
      "base-uri 'self'",
      // Upgrade insecure requests in production
      process.env.NODE_ENV === "production" ? "upgrade-insecure-requests" : "",
    ].filter(Boolean).join("; "),
  },
];

const nextConfig: NextConfig = {
  // 生产环境使用 standalone 输出模式（Docker 部署必须）
  output: "standalone",

  // Turbopack 根目录设置 - 解决多个 lockfile 的警告
  turbopack: {
    root: __dirname,
  },

  // outputFileTracingRoot is set during Docker build via sed
  // Default to /app for production, but let Next.js auto-detect for standalone
  outputFileTracingRoot: process.env.OUTPUT_FILE_TRACING_ROOT || undefined,

  /** Baked into Edge middleware at build so JWT issuer/aud matches on Vercel. */
  env: {
    MIDDLEWARE_FIREBASE_PROJECT_ID:
      process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID ||
      process.env.FIREBASE_PROJECT_ID ||
      "",
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  serverExternalPackages: ["genkit", "@genkit-ai/*", "handlebars"],
  webpack: (config, { isServer }) => {
    // 排除服务端专用包，防止它们被打包到客户端
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
      };
      
      // 将 genkit 相关包标记为外部依赖，不打包到客户端
      config.externals = [
        ...(config.externals || []),
        "genkit",
        "@genkit-ai/core",
        "@genkit-ai/ai",
        "@genkit-ai/dotprompt",
        "@genkit-ai/evaluator",
        "@genkit-ai/flow",
        "handlebars",
      ];
    } else {
      // Server-side: provide Buffer polyfill for firebase-admin dependencies
      config.resolve.fallback = {
        ...config.resolve.fallback,
        buffer: "buffer",
      };
    }
    
    return config;
  },
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "@radix-ui/react-icons",
      "date-fns",
      "framer-motion",
      "recharts",
      "react-icons",
    ],
  },
  compiler: {
    removeConsole:
      process.env.NODE_ENV === "production"
        ? {
            exclude: ["error", "warn"],
          }
        : false,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "placehold.co",
        port: "",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "i.postimg.cc",
        port: "",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "res.cloudinary.com",
        port: "",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "firebasestorage.googleapis.com",
        port: "",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
        port: "",
        pathname: "/**",
      },
    ],
  },
  allowedDevOrigins: [
    "http://localhost:9002",
    "http://127.0.0.1:9002",
    "https://6000-firebase-studio-1753536684062.cluster-fkltigo73ncaixtmokrzxhwsfc.cloudworkstations.dev",
    "zermin.cloud",
  ],
  // Security headers
  async headers() {
    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
