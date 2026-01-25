import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

/**
 * NextAuth.js 設定
 * ローカル開発環境で Google OAuth 認証を提供
 * 本番環境では Cloud IAP が認証を担当
 */
const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  pages: {
    signIn: "/admin/login",
  },
  callbacks: {
    async session({ session, token }) {
      // セッションにユーザー情報を追加
      if (session.user && token.sub) {
        session.user.id = token.sub;
      }
      return session;
    },
  },
});

export { handler as GET, handler as POST };
