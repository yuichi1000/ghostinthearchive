import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // SSG (Static Site Generation) - 完全静的出力
  output: "export",

  // 静的エクスポート時は画像最適化を無効化
  images: {
    unoptimized: true,
  },

  // 末尾スラッシュを追加（Firebase Hosting との互換性）
  trailingSlash: true,
};

export default nextConfig;
