import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // @ghost/shared パッケージをトランスパイル
  transpilePackages: ["@ghost/shared"],

  // Turbopack のルートディレクトリを monorepo ルートに設定（共有パッケージの解決に必要）
  turbopack: {
    root: path.resolve(__dirname, ".."),
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
      // 開発環境: Firebase Storage エミュレータ
      {
        protocol: "http",
        hostname: "localhost",
        port: "9199",
        pathname: "/v0/b/**",
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
