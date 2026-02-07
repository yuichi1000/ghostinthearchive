"use client";

import { SessionProvider as NextAuthSessionProvider } from "next-auth/react";
import type { ReactNode } from "react";

interface SessionProviderProps {
  children: ReactNode;
}

/**
 * NextAuth.js SessionProvider ラッパー
 * クライアントコンポーネントとして分離
 */
export function SessionProvider({ children }: SessionProviderProps) {
  return <NextAuthSessionProvider>{children}</NextAuthSessionProvider>;
}
