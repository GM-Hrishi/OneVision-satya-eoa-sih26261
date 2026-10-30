// RB-06 Verification panel (UI spec §6.4, §7.2, wireframe W1): one row per document with exactly one
// of the six labels, the source checked (Simulated source tag for mock adapters), both signature
// badges and the time of the check; label counts; the checks and findings behind each label; the
// signature-to-label mapping legend. Advisory only: nothing here approves, rejects or clears.
import type { CaseVerification, CaseVerificationDocument, Check, Flag } from "@satya/shared-types";
import { getLocale, getTranslations } from "next-intl/server";
import { FlagCard, Label } from "@/components/diff/DiffView";
import styles from "@/components/diff/DiffView.module.css";
import { SignatureBadge } from "@/components/signature/SignatureBadge";
import { SourceTag } from "@/components/ui/SourceTag";
import { StatusLabel } from "@/components/ui/StatusLabel";
import { LABEL_ORDER } from "@/lib/labels";
import { ReasonLine } from "@/components/demo/ReasonLine";
import own from "./VerificationPanel.module.css";

type TV = Awaited<ReturnType<typeof getTranslations<"verification">>>;
const KNOWN_SOURCES = new Set([
  "pdf-signature",
  "icai-udin",
  "cca-offline-chain",
  "shcil-estamp-mock",
  "icai-udin-mock",
]);

function formatIst(iso: string, locale: string): string {
  return new Intl.DateTimeFormat(locale === "hi" ? "hi-IN" : "en-IN", {
    timeZone: "Asia/Kolkata",
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}

function sourceText(doc: CaseVerificationDocument, tv: TV): string {
  const channel = doc.source.channel;
  return KNOWN_SOURCES.has(channel) ? tv(`source.${channel}` as never) : tv("source.other", { channel });
}

function reasonText(check: Check, tv: TV): string {
  const key = `reason.${check.reason_code}`;
  return tv.has(key as never) ? tv(key as never) : check.reason_code;
}

export async function VerificationPanel({ data }: { data: CaseVerification }) {
  const tv = await getTranslations("verification");
  const td = await getTranslations("diff");
  const tr = await getTranslations("rules");
  const locale = await getLocale();
  return (
    <>
      <section className={styles.section} aria-labelledby="ver-counts">
        <h2 id="ver-counts">{tv("countsHeading")}</h2>
        <p className={styles.note}>{tv("countsNote")}</p>
        <ul className={own.counts}>
          {LABEL_ORDER.map((label) => (
            <li key={label}>
              <StatusLabel label={label} count={data.label_counts[label]} />
            </li>
          ))}
        </ul>
        <p className={styles.note}>{tv("lastRun", { at: formatIst(data.last_full_run_at, locale) })}</p>
      </section>

      <section className={styles.section} aria-labelledby="ver-docs">
        <h2 id="ver-docs">{tv("tableHeading")}</h2>
        {data.documents.length === 0 ? (
          <p>{tv("noDocuments")}</p>
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th scope="col">{tv("colDocument")}</th>
                  <th scope="col">{tv("colIssuer")}</th>
                  <th scope="col">{tv("colSource")}</th>
                  <th scope="col">{tv("colResult")}</th>
                  <th scope="col">{tv("colIssuerSig")}</th>
                  <th scope="col">{tv("colUploaderSig")}</th>
                  <th scope="col">{tv("colChecked")}</th>
                  <th scope="col">{tv("colFindings")}</th>
                </tr>
              </thead>
              <tbody>
                {data.documents.map((doc) => (
                  <tr key={doc.doc_id}>
                    <th scope="row" className={own.docCell}>
                      {doc.title}
                      <span className={own.slot}>{doc.slot}</span>
                    </th>
                    <td>{doc.issuer_profile ?? <span className={styles.muted}>{tv("issuerProfilePending")}</span>}</td>
                    <td>
                      {sourceText(doc, tv)}{" "}
                      {doc.source.adapter_mode === "mock" ? (
                        <SourceTag kind="simulated" />
                      ) : doc.source.channel === "pdf-signature" || doc.source.channel === "cca-offline-chain" ? (
                        <SourceTag kind="testAnchor" />
                      ) : (
                        <span className={styles.label} data-tone="neutral">
                          {tv(`mode.${doc.source.adapter_mode}`)}
                        </span>
                      )}
                    </td>
                    <td>
                      {doc.label === "not_applicable" ? (
                        <Label tone="neutral">{tv("notApplicable")}</Label>
                      ) : (
                        <StatusLabel label={doc.label} size="sm" />
                      )}
                    </td>
                    <td>
                      <SignatureBadge sig={doc.issuer_sig} />
                    </td>
                    <td>
                      <SignatureBadge sig={doc.uploader_sig} />
                    </td>
                    <td className={own.nowrap}>{formatIst(doc.checked_at, locale)}</td>
                    <td className={styles.num}>{tv("findings", { count: doc.flag_count })}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className={styles.note}>
          {tv("actionsNote", {
            actions: [...new Set(data.documents.flatMap((d) => d.actions))].map((a) => tv(`action.${a}`)).join(", "),
          })}
        </p>
      </section>

      <section className={styles.section} aria-labelledby="ver-details">
        <h2 id="ver-details">{tv("detailsHeading")}</h2>
        {data.documents.map((doc) => (
          <DocumentDetails key={doc.doc_id} doc={doc} tv={tv} td={td} tr={tr} />
        ))}
      </section>

      <section className={styles.section} aria-labelledby="ver-legend">
        <h2 id="ver-legend">{tv("legendHeading")}</h2>
        <ul className={own.legend}>
          {(["verified", "mismatch", "expired", "manual", "unavailable", "absent"] as const).map((k) => (
            <li key={k}>{tv(`legend.${k}`)}</li>
          ))}
        </ul>
        <p className={styles.note}>{tv("legendUploader")}</p>
        <p className={styles.note}>{tv("legendAnchor")}</p>
      </section>
    </>
  );
}

async function DocumentDetails({
  doc,
  tv,
  td,
  tr,
}: {
  doc: CaseVerificationDocument;
  tv: TV;
  td: Awaited<ReturnType<typeof getTranslations<"diff">>>;
  tr: Awaited<ReturnType<typeof getTranslations<"rules">>>;
}) {
  const checks: Check[] = doc.checks ?? [];
  const flags: Flag[] = doc.flags ?? [];
  return (
    <details className={own.details}>
      <summary>{tv("checksSummary", { title: doc.title, count: checks.length, flags: flags.length })}</summary>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col">{tv("colCheck")}</th>
              <th scope="col">{tv("colOutcome")}</th>
              <th scope="col">{tv("colReason")}</th>
              <th scope="col">{tv("colEvidence")}</th>
            </tr>
          </thead>
          <tbody>
            {checks.map((check, i) => (
              <tr key={`${check.kind}-${check.reason_code}-${i}`}>
                <td>{tv(`kind.${check.kind}`)}</td>
                <td>
                  <StatusLabel label={check.outcome} size="sm" />
                </td>
                <td>
                  <ReasonLine code={check.reason_code} read={doc.read} fallback={reasonText(check, tv)} />
                </td>
                <td>{check.evidence ? tv("evidencePage", { page: check.evidence.page }) : tv("noEvidence")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {flags.length ? (
        <ol className={styles.flags}>
          {flags.map((flag) => (
            <li key={flag.flag_id}>
              <FlagCard flag={flag} t={td} title={tr(flag.rule_text_key as never)} />
            </li>
          ))}
        </ol>
      ) : null}
    </details>
  );
}
