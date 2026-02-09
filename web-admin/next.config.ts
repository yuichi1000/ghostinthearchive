import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Turbopack のルートディレクトリを明示（親ディレクトリの lockfile 誤検知を防止）
  turbopack: {
    root: path.resolve(__dirname),
  },
  // 画像最適化
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "firebasestorage.googleapis.com",
        pathname: "/v0/b/**",
      },
      {
        protocol: "https",
        hostname: "storage.googleapis.com",
        pathname: "/**",
      },
    ],
  },

  // セキュリティヘッダー
  headers: async () => [
    {
      source: "/:path*",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "X-Robots-Tag", value: "noindex, nofollow" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      ],
    },
  ],

  // Cloud Run 用のスタンドアロン出力
  output: "standalone",
};

export default nextConfig;
