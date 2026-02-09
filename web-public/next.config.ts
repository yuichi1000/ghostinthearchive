import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // SSG (Static Site Generation) - 本番ビルド時のみ完全静的出力
  // dev モードでは動的レンダリングを許可（ローカル開発で Firestore 直接参照）
  ...(process.env.NODE_ENV === "production" ? { output: "export" as const } : {}),

  // Turbopack のルートディレクトリを明示（親ディレクトリの lockfile 誤検知を防止）
  turbopack: {
    root: path.resolve(__dirname),
  },

  // 静的エクスポート時は画像最適化を無効化
  images: {
    unoptimized: true,
  },

  // 末尾スラッシュを追加（Firebase Hosting との互換性）
  trailingSlash: true,
};

export default nextConfig;
