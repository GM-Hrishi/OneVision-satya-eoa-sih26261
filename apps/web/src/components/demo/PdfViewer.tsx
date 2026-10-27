"use client";
// PDF.js viewer: renders one page of a stored synthetic PDF and outlines the evidence regions of a
// flag (normalised 0..1, origin top left). The PDF comes from the workbench's own /pdf route.
import { useEffect, useRef, useState } from "react";
import { SourceTag } from "@/components/ui/SourceTag";
import styles from "./Demo.module.css";

export interface ViewerTarget {
  caseId: string;
  docId: string;
  page: number;
  regions: { x: number; y: number; w: number; h: number }[];
  label: string;
}

export interface ViewerText {
  title: string;
  empty: string;
  loading: string;
  failed: string;
  page: string;
  prev: string;
  next: string;
}

export function PdfViewer({ target, text }: { target: ViewerTarget | null; text: ViewerText }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const firstRegion = useRef<HTMLDivElement>(null);
  // The parent remounts this component (key) when the target document or page changes.
  const [page, setPage] = useState(target?.page ?? 1);
  const [pages, setPages] = useState(0);
  const [state, setState] = useState<"loading" | "ready" | "failed">("loading");
  const url = target ? `/pdf/${target.caseId}/${target.docId}` : null;

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    (async () => {
      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();
        const doc = await pdfjs.getDocument({ url, ...({ isEvalSupported: false } as object) }).promise;
        if (cancelled) return;
        setPages(doc.numPages);
        const pdfPage = await doc.getPage(Math.min(Math.max(page, 1), doc.numPages));
        const viewport = pdfPage.getViewport({ scale: 1.6 });
        const el = canvas.current;
        if (!el || cancelled) return;
        el.width = viewport.width;
        el.height = viewport.height;
        await pdfPage.render({ canvas: el, viewport }).promise;
        if (!cancelled) {
          setState("ready");
          firstRegion.current?.scrollIntoView({ block: "center", behavior: "auto" });
        }
      } catch {
        if (!cancelled) setState("failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [url, page]);

  if (!target) {
    return (
      <div className={styles.viewer}>
        <p>{text.empty}</p>
      </div>
    );
  }
  const regions = page === target.page ? target.regions : [];
  return (
    <div className={styles.viewer} aria-label={text.title}>
      <div className={styles.viewerBar}>
        <strong>{target.label}</strong>
        <SourceTag kind="testAnchor" />
        <span>{text.page.replace("{page}", String(page)).replace("{pages}", String(pages || "?"))}</span>
        <button type="button" className={styles.linkButton} disabled={page <= 1} onClick={() => setPage(page - 1)}>
          {text.prev}
        </button>
        <button type="button" className={styles.linkButton} disabled={pages === 0 || page >= pages} onClick={() => setPage(page + 1)}>
          {text.next}
        </button>
      </div>
      {state === "loading" ? <p role="status">{text.loading}</p> : null}
      {state === "failed" ? <p role="alert" className={styles.error}>{text.failed}</p> : null}
      <div className={styles.pageWrap}>
        <div className={styles.pageInner}>
          <canvas ref={canvas} aria-label={target.label} role="img" />
          {regions.map((r, i) => (
            <div
              key={i}
              ref={i === 0 ? firstRegion : undefined}
              className={styles.region}
              style={{ left: `${r.x * 100}%`, top: `${r.y * 100}%`, width: `${r.w * 100}%`, height: `${r.h * 100}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
