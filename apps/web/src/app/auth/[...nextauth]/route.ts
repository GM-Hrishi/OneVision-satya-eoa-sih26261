import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth";

const handler = (req: Request, ctx: { params: Promise<{ nextauth: string[] }> }) =>
  NextAuth(authOptions())(req, ctx);

export { handler as GET, handler as POST };
