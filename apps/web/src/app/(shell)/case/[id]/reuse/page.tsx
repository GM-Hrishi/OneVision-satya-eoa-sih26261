// Reuse graph (VISUAL 6), behind features.reuseGraph. Off in every real build: no API provides the cross-case
// fingerprint index yet, so the route answers a real 404 and is in no navigation. In development with
// NEXT_PUBLIC_UI_FIXTURES=1 it shows a clearly labelled fixture.
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { ReuseGraph } from "@/components/k/ReuseGraph";
import fixture from "@/lib/api/__fixtures__/reuse-index.dev.json";
import { buildReuseGraph, type ReuseIndex } from "@/lib/api/k-adapters/reuse";
import { features } from "@/lib/features";
import { requireRole } from "@/lib/session";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("k.reuse");
  return { title: t("title"), description: t("description") };
}

export default async function ReusePage({ params }: Props) {
  if (!features.reuseGraph) notFound();
  const { id } = await params;
  await requireRole("RB", `/case/${id}/reuse`);
  const t = await getTranslations("k.reuse");
  const graph = buildReuseGraph(fixture as unknown as ReuseIndex);
  return (
    <>
      <header>
        <h1>{t("headline", { count: graph.shared })}</h1>
        <p className="k-label">{t("devNote")}</p>
        <p>
          <Link href={`/case/${id}`}>{t("back")}</Link>
        </p>
      </header>
      <ReuseGraph graph={graph} />
    </>
  );
}
