"use client";
// React Aria links use the Next router for client-side navigation.
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { RouterProvider } from "react-aria-components";

export function Providers({ children }: { children: ReactNode }) {
  const router = useRouter();
  return <RouterProvider navigate={(href) => router.push(String(href))}>{children}</RouterProvider>;
}
