// RB-05 Affidavit DiffView (UI spec §6.3, §7.1): header cards, structure check, clause-by-clause
// diff, table reconciliation vs Application Report data, stamp/signing order, flag rail.
// Server component; every string comes from the "diff" messages (English + Hindi).
import type {
  AffidavitDiff,
  AffidavitTable,
  AffidavitTableRow,
  DiffOp,
  Flag,
  SwornDeclaration,
} from "@satya/shared-types";
import { getTranslations } from "next-intl/server";
import Link from "next/link";
import type { ReactNode } from "react";
import { SignatureBadge } from "@/components/signature/SignatureBadge";
import { SourceTag } from "@/components/ui/SourceTag";
import { StatusLabel } from "@/components/ui/StatusLabel";
import styles from "./DiffView.module.css";

type T = Awaited<ReturnType<typeof getTranslations<"diff">>>;
type ReadT = Awaited<ReturnType<typeof getTranslations<"demo.ocr">>>;
export type Tone = "mismatch" | "manual" | "ok" | "neutral";

const VALUE_PREVIEW = 160;
const SEVERITY_ORDER = { critical: 0, warning: 1, info: 2 } as const;

export function Label({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <span className={styles.label} data-tone={tone}>
      {children}
    </span>
  );
}

export function labelTone(label: Flag["label"]): Tone {
  if (label === "mismatch_detected" || label === "expired") return "mismatch";
  if (label === "manual_review_required") return "manual";
  if (label === "verified") return "ok";
  return "neutral";
}

/** A masked identifier: bullets are hidden from screen readers, which hear "masked, ends in …". */
function Cell({ value, t }: { value: string | null | undefined; t: T }) {
  if (value == null || value === "") return <span className={styles.muted}>{t("none")}</span>;
  if (value.startsWith("•")) {
    const tail = value.replace(/•/g, "");
    return (
      <>
        <span aria-hidden="true" className={styles.mono}>
          {value}
        </span>
        <span className={styles.srOnly}>{tail ? t("maskedEnding", { tail }) : t("masked")}</span>
      </>
    );
  }
  return <>{value}</>;
}

function preview(value: Flag["extracted_value"]): string | null {
  if (value === null || value === undefined) return null;
  const text = String(value);
  return text.length > VALUE_PREVIEW ? `${text.slice(0, VALUE_PREVIEW)}…` : text;
}

function declLabel(t: T, block: string, no: number): string {
  if (block === "existing_institute") return t("declExisting", { no });
  if (block === "extra") return t("declExtra", { no });
  return t("declCore", { no });
}

export async function DiffView({ diff, showAll, allHref, changedHref, verificationHref }: {
  diff: AffidavitDiff;
  showAll: boolean;
  allHref: string;
  changedHref: string;
  verificationHref?: string;
}) {
  const t = await getTranslations("diff");
  const tr = await getTranslations("rules");
  const to = await getTranslations("demo.ocr");
  const flagsById = new Map(diff.flags.map((f) => [f.flag_id, f]));
  const flags = [...diff.flags].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity] || (a.page ?? 0) - (b.page ?? 0),
  );
  const changes = diff.ops.filter((o) => o.op !== "equal");
  const ops = showAll ? diff.ops : changes;
  const expectedByNo = new Map(diff.expected.declarations.map((d) => [d.no, d]));
  const swornByNo = new Map(diff.sworn.declarations.map((d) => [d.no, d]));
  const pending = new Set(diff.pending.map((p) => p.section));
  // B-43: "matches" is said only when the comparison really ran on a text layer and the structure
  // check found everything. Without an explicit state the page assumes nothing was compared.
  const state = comparisonState(diff);
  const complete = structureComplete(diff);
  const showResults = state.compared || state.ocrText;
  const clean = state.compared && complete;

  return (
    <div className={styles.layout}>
      <div className={styles.mainCol}>
        <section className={styles.section} aria-labelledby="diff-cards">
          <h2 id="diff-cards">{t("cardsHeading")}</h2>
          <div className={styles.cards}>
            <div className={styles.card}>
              <h3>{t("expectedHeading")}</h3>
              <dl className={styles.facts}>
                <dt>{t("template")}</dt>
                <dd className={styles.mono}>{diff.expected.template_id}</dd>
                <dt>{t("templateYear")}</dt>
                <dd>{diff.expected.template_year}</dd>
                <dt>{t("applicationId")}</dt>
                <dd className={styles.mono}>{diff.expected.aid}</dd>
                <dt>{t("categoryList")}</dt>
                <dd>{diff.expected.category_list.join("; ")}</dd>
                <dt>{t("contents")}</dt>
                <dd>{t("contentsValue", { count: diff.expected.declarations.length })}</dd>
              </dl>
            </div>
            <div className={styles.card}>
              <h3>{t("swornHeading")}</h3>
              <dl className={styles.facts}>
                <dt>{t("pages")}</dt>
                <dd>{diff.sworn.page_count}</dd>
                <dt>{t("textSource")}</dt>
                <dd>{t(`source.${state.source}` as never, state.values as never)}</dd>
                <dt>{t("templateMatch")}</dt>
                <dd>
                  {!state.compared ? (
                    <Label tone="neutral">{t("notChecked")}</Label>
                  ) : diff.sworn.template_match ? (
                    <Label tone="ok">{t("templateMatchYes")}</Label>
                  ) : (
                    <Label tone="manual">{t("templateMatchNo")}</Label>
                  )}
                </dd>
                <dt>{t("sha256")}</dt>
                <dd className={styles.mono}>{diff.sworn.sha256}</dd>
                {pending.has("signatures") ? (
                  <>
                    <dt>{t("signatures")}</dt>
                    <dd>{t("signaturesPending")}</dd>
                  </>
                ) : (
                  <>
                    <dt>{t("issuerSignature")}</dt>
                    <dd>
                      <SignatureBadge sig={diff.sworn.issuer_sig} />
                    </dd>
                    <dt>{t("uploaderSignature")}</dt>
                    <dd>
                      <SignatureBadge sig={diff.sworn.uploader_sig} />
                    </dd>
                  </>
                )}
              </dl>
            </div>
          </div>
        </section>

        {!state.compared ? <NotCompared state={state} t={t} to={to} /> : null}

        <Structure diff={diff} t={t} showResults={showResults} />

        <section className={styles.section} aria-labelledby="diff-clauses">
          <h2 id="diff-clauses">{t("clausesHeading")}</h2>
          {!showResults ? (
            <p>{t("clausesNotCompared")}</p>
          ) : (
            <>
              <p className={styles.note}>
                {t("normalisation", {
                  hyphens: diff.normalisation.hyphens_rejoined,
                  struck: diff.normalisation.strike_through_resolved,
                  order: diff.normalisation.date_order,
                })}
              </p>
              <div className={styles.toggle}>
                {clean || changes.length > 0 ? (
                  <span>{t("changesCount", { count: changes.length, total: diff.expected.declarations.length })}</span>
                ) : null}
                {showAll ? <a href={changedHref}>{t("showChanged")}</a> : <a href={allHref}>{t("showAll")}</a>}
              </div>
            </>
          )}
          {!showResults ? null : ops.length === 0 ? (
            <p>{clean ? t("noChanges") : t("clausesIncomplete")}</p>
          ) : (
            <ol className={styles.ops}>
              {ops.map((op, i) => (
                <OpItem
                  key={`${op.decl_no ?? "x"}-${op.sworn_no ?? "x"}-${i}`}
                  op={op}
                  t={t}
                  expected={op.decl_no ? expectedByNo.get(op.decl_no) : undefined}
                  sworn={op.sworn_no ? swornByNo.get(op.sworn_no) : undefined}
                  flag={op.flag_id ? flagsById.get(op.flag_id) : undefined}
                />
              ))}
            </ol>
          )}
        </section>

        <section className={styles.section} aria-labelledby="diff-tables">
          <h2 id="diff-tables">{t("tablesHeading")}</h2>
          {state.compared ? (
            <>
              <p className={styles.note}>{t("tablesIntro")}</p>
              {diff.tables.map((table) => (
                <ReconTable key={table.table} table={table} t={t} />
              ))}
            </>
          ) : (
            <p>{t("tablesNotCompared")}</p>
          )}
        </section>

        <section className={styles.section} aria-labelledby="diff-stamp">
          <h2 id="diff-stamp">{t("stampHeading")}</h2>
          {pending.has("stamp") ? (
            <p>{t("stampPending")}</p>
          ) : (
            <StampAndOrder diff={diff} t={t} />
          )}
          {verificationHref ? (
            <p className={styles.note}>
              <Link href={verificationHref}>{t("openVerification")}</Link>
            </p>
          ) : null}
        </section>
      </div>

      <aside className={styles.rail} aria-labelledby="diff-flags">
        <h2 id="diff-flags">{t("flagsHeading", { count: flags.length })}</h2>
        {flags.length === 0 ? (
          <p className={styles.section}>
            {clean ? t("noFlags") : state.compared ? t("noFlagsIncomplete") : t("noFlagsNotCompared")}
          </p>
        ) : (
          <ol className={styles.flags}>
            {flags.map((flag) => (
              <li key={flag.flag_id}>
                <FlagCard flag={flag} t={t} title={tr(flag.rule_text_key as never)} />
              </li>
            ))}
          </ol>
        )}
      </aside>
    </div>
  );
}

/** Stamp page fields, notary seal and the signing order (UI spec §7.1 item 5; M6, P-4). */
function StampAndOrder({ diff, t }: { diff: AffidavitDiff; t: T }) {
  const stamp = diff.stamp;
  const chrono = diff.chronology;
  const steps = chrono
    ? ([
        ["application", chrono.application_date],
        ["stamp", chrono.stamp_date],
        ["notarisation", chrono.notary_date],
        ["dsc", chrono.dsc_date ?? null],
        ["upload", chrono.upload_date],
      ] as const)
    : [];
  return (
    <>
      <h3>{t("stampDetails")}</h3>
      {stamp ? (
        <dl className={styles.facts}>
          <dt>{t("stampChecks")}</dt>
          <dd>
            <StatusLabel label={stamp.state} size="sm" />
            <span className={styles.expectedValue}>{t("stampStateNote")}</span>
          </dd>
          <dt>{t("stampInstrument")}</dt>
          <dd>{t(`instrument.${stamp.instrument}` as never)}</dd>
          <dt>{t("certificateNo")}</dt>
          <dd>
            <Cell value={stamp.certificate_no} t={t} />
          </dd>
          <dt>{t("stampIssued")}</dt>
          <dd>{stamp.issue_date ?? t("notStated")}</dd>
          <dt>{t("article")}</dt>
          <dd>{stamp.article ?? t("notStated")}</dd>
          <dt>{t("secondParty")}</dt>
          <dd>{stamp.second_party ?? t("notStated")}</dd>
          <dt>{t("duty")}</dt>
          <dd>{stamp.duty == null ? t("notStated") : t("dutyValue", { amount: stamp.duty / 100 })}</dd>
        </dl>
      ) : (
        <p>{t("noStamp")}</p>
      )}
      <h3>{t("orderHeading")}</h3>
      {chrono ? (
        <>
          <p className={styles.note}>{t("orderRule")}</p>
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th scope="col">{t("orderStep")}</th>
                  <th scope="col">{t("orderDate")}</th>
                </tr>
              </thead>
              <tbody>
                {steps.map(([step, value]) => (
                  <tr key={step}>
                    <th scope="row">
                      {t(`step.${step}`)}
                      {step === "dsc" && chrono.dsc_kind ? (
                        <span className={styles.expectedValue}>{t(`dscKind.${chrono.dsc_kind}`)}</span>
                      ) : null}
                    </th>
                    <td className={styles.mono}>{value ?? t("notStated")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p>
            {chrono.order_ok === null ? (
              <Label tone="neutral">{t("orderUnknown")}</Label>
            ) : chrono.order_ok ? (
              <Label tone="ok">{t("orderOk")}</Label>
            ) : (
              <Label tone="manual">{t("orderBroken")}</Label>
            )}{" "}
            {chrono.mark_after_notary === true ? <Label tone="manual">{t("markAfter")}</Label> : null}
            {chrono.mark_after_notary === false ? <Label tone="ok">{t("markOk")}</Label> : null}
          </p>
          <dl className={styles.facts}>
            <dt>{t("notarySeal")}</dt>
            <dd>
              {chrono.notary_expiry ?? t("notStated")}{" "}
              {chrono.notary_expiry_ok === true ? <Label tone="ok">{t("sealOk")}</Label> : null}
              {chrono.notary_expiry_ok === false ? <Label tone="mismatch">{t("sealExpired")}</Label> : null}
            </dd>
          </dl>
        </>
      ) : (
        <p>{t("notStated")}</p>
      )}
    </>
  );
}

type ComparisonView = {
  compared: boolean;
  ocrText: boolean;
  source: string;
  values: Record<string, string | number>;
  why: string | null;
};

/** What the page may claim about this copy (D1 of B-43). A missing state counts as not compared. */
function comparisonState(diff: AffidavitDiff): ComparisonView {
  const c = diff.comparison;
  if (!c) {
    const layer = diff.sworn.text_source === "text_layer";
    return { compared: false, ocrText: !layer, source: layer ? "text_layer" : "scan_read", values: {}, why: null };
  }
  const confidence = c.read.ocr_mean_confidence == null ? undefined : Math.round(c.read.ocr_mean_confidence * 100);
  return {
    compared: c.state === "compared",
    ocrText: c.source === "scan_read" || c.source === "scan_unreliable",
    source: c.source,
    values: { ...c.read.values, ...(confidence === undefined ? {} : { confidence }), max_pages: 50 },
    why: c.read.variant,
  };
}

function structureComplete(diff: AffidavitDiff): boolean {
  const s = diff.structure;
  return (
    s.category_line.state === "present" &&
    s.core.expected === s.core.found &&
    s.existing_institute.expected === s.existing_institute.found &&
    s.extra_blocks.length === 0
  );
}

/** Says plainly that nothing was compared, and why (the reading sentence comes from the read). */
function NotCompared({ state, t, to }: { state: ComparisonView; t: T; to: ReadT }) {
  return (
    <section className={styles.section} aria-labelledby="diff-notcompared">
      <h2 id="diff-notcompared">{t("notComparedHeading")}</h2>
      {state.why ? <p>{to(`why.${state.why}` as never, state.values as never)}</p> : null}
      <p className={styles.note}>{state.ocrText ? t("notComparedOcr") : t("notComparedEmpty")}</p>
    </section>
  );
}

function Structure({ diff, t, showResults }: { diff: AffidavitDiff; t: T; showResults: boolean }) {
  const s = diff.structure;
  const categoryState = s.category_line.state;
  const tone: Tone = categoryState === "present" ? "ok" : "mismatch";
  const blockOk = (b: { expected: number; found: number }) => b.expected === b.found;
  if (!showResults) {
    const rows = [
      [t("categoryLine"), s.category_line.expected.join("; ")],
      [t("block.core"), String(s.core.expected)],
      [t("block.existing_institute"), String(s.existing_institute.expected)],
      [t("extraBlocks"), t("noneExpected")],
    ];
    return (
      <section className={styles.section} aria-labelledby="diff-structure">
        <h2 id="diff-structure">{t("structureHeading")}</h2>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th scope="col">{t("check")}</th>
                <th scope="col">{t("expected")}</th>
                <th scope="col">{t("found")}</th>
                <th scope="col">{t("result")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(([name, expected]) => (
                <tr key={name}>
                  <th scope="row">{name}</th>
                  <td>{expected}</td>
                  <td colSpan={2}>
                    <Label tone="neutral">{t("notChecked")}</Label>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    );
  }
  return (
    <section className={styles.section} aria-labelledby="diff-structure">
      <h2 id="diff-structure">{t("structureHeading")}</h2>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th scope="col">{t("check")}</th>
              <th scope="col">{t("expected")}</th>
              <th scope="col">{t("found")}</th>
              <th scope="col">{t("result")}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th scope="row">{t("categoryLine")}</th>
              <td>{s.category_line.expected.join("; ")}</td>
              <td>
                {s.category_line.found.length ? (
                  s.category_line.found.join("; ")
                ) : (
                  <span className={styles.wrong}>{t("notFound")}</span>
                )}
              </td>
              <td>
                <Label tone={tone}>{t(`categoryState.${categoryState}`)}</Label>
                {s.category_line.page ? (
                  <span className={styles.expectedValue}>{t("onPage", { page: s.category_line.page })}</span>
                ) : null}
              </td>
            </tr>
            {(["core", "existing_institute"] as const).map((block) => (
              <tr key={block}>
                <th scope="row">{t(`block.${block}`)}</th>
                <td className={styles.num}>{s[block].expected}</td>
                <td className={styles.num}>
                  {blockOk(s[block]) ? s[block].found : <span className={styles.wrong}>{s[block].found}</span>}
                </td>
                <td>
                  <Label tone={blockOk(s[block]) ? "ok" : "mismatch"}>
                    {blockOk(s[block]) ? t("complete") : t("incomplete")}
                  </Label>
                </td>
              </tr>
            ))}
            <tr>
              <th scope="row">{t("extraBlocks")}</th>
              <td>{t("noneExpected")}</td>
              <td>
                {s.extra_blocks.length
                  ? s.extra_blocks.map((b) => `${b.heading} (${t("onPage", { page: b.page })})`).join("; ")
                  : t("none")}
              </td>
              <td>
                {s.extra_blocks.length ? (
                  <Label tone="mismatch">{t("extraBlockPresent")}</Label>
                ) : (
                  <Label tone="ok">{t("noExtraBlock")}</Label>
                )}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}

function OpItem({ op, t, expected, sworn, flag }: {
  op: DiffOp;
  t: T;
  expected?: { no: number; printed_no: number; block: string };
  sworn?: SwornDeclaration;
  flag?: Flag;
}) {
  const label = expected
    ? declLabel(t, expected.block, expected.printed_no)
    : sworn
      ? declLabel(t, sworn.block, sworn.printed_no ?? sworn.no)
      : t("declUnknown");
  const tone: Tone = op.op === "equal" ? "ok" : op.op === "added" ? "manual" : "mismatch";
  return (
    <li className={styles.op} id={op.decl_no ? `decl-${op.decl_no}` : undefined}>
      <div className={styles.opHead}>
        <strong>{label}</strong>
        <Label tone={tone}>{t(`op.${op.op}`)}</Label>
        {sworn ? <span className={styles.muted}>{t("swornPage", { page: sworn.page })}</span> : null}
        {flag ? <span className={styles.mono}>{flag.flag_id.slice(-6)}</span> : null}
      </div>
      <p className={styles.opText}>
        {op.spans.map((span, i) => {
          if (span.kind === "delete")
            return (
              <del key={i} className={styles.del}>
                <span className={styles.srOnly}>{t("deletedPrefix")}</span>
                {span.text}
              </del>
            );
          if (span.kind === "insert")
            return (
              <ins key={i} className={styles.ins}>
                <span className={styles.srOnly}>{t("insertedPrefix")}</span>
                {span.text}
              </ins>
            );
          return <span key={i}>{span.text}</span>;
        }).reduce<ReactNode[]>((acc, node, i) => (i ? [...acc, " ", node] : [node]), [])}
      </p>
    </li>
  );
}

function rowState(t: T, row: AffidavitTableRow) {
  const tone: Tone = row.state === "matched" ? "ok" : "mismatch";
  return <Label tone={tone}>{t(`rowState.${row.state}`)}</Label>;
}

function ReconTable({ table, t }: { table: AffidavitTable; t: T }) {
  const captionId = `table-${table.table}`;
  return (
    <>
      <h3 id={captionId}>{t(`tables.${table.table}`)}</h3>
      {table.rows.length === 0 ? (
        <p className={styles.muted}>{t("emptyTable")}</p>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table} aria-labelledby={captionId}>
            <thead>
              <tr>
                {table.columns.map((c) => (
                  <th key={c} scope="col">
                    {t(`columns.${c}`)}
                  </th>
                ))}
                <th scope="col">{t("result")}</th>
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row) => (
                <tr key={`${row.key}-${row.state}`}>
                  {table.columns.map((c, i) => {
                    const sworn = row.sworn_cells[i];
                    const report = row.application_report_cells[i];
                    const mismatch = row.cell_match[i] === false;
                    return (
                      <td key={c} className={c.endsWith("acre") || c.endsWith("m2") ? styles.num : undefined}>
                        {mismatch ? (
                          <>
                            <span className={styles.wrong}>
                              <Cell value={sworn} t={t} />
                            </span>
                            <span className={styles.expectedValue}>
                              {t("reportValue")} <Cell value={report} t={t} />
                            </span>
                            {row.delta != null && (c === "area_acre" || c === "carpet_area_m2") ? (
                              <span className={styles.difference}>
                                {t("difference", { delta: row.delta > 0 ? `+${row.delta}` : String(row.delta) })}
                              </span>
                            ) : null}
                          </>
                        ) : (
                          <Cell value={sworn ?? report} t={t} />
                        )}
                      </td>
                    );
                  })}
                  <td>
                    {rowState(t, row)}
                    {row.page ? <span className={styles.expectedValue}>{t("onPage", { page: row.page })}</span> : null}
                  </td>
                </tr>
              ))}
            </tbody>
            {table.table === "land" ? (
              <tfoot>
                <tr>
                  <td colSpan={table.columns.length - 1}>{t("computedTotal")}</td>
                  <td className={styles.num}>
                    {table.computed_total_acres !== table.expected_total_acres ? (
                      <>
                        <span className={styles.wrong}>{table.computed_total_acres?.toFixed(2) ?? t("none")}</span>
                        <span className={styles.expectedValue}>
                          {t("reportValue")} {table.expected_total_acres?.toFixed(2) ?? t("none")}
                        </span>
                      </>
                    ) : (
                      table.computed_total_acres?.toFixed(2)
                    )}
                  </td>
                  <td>
                    <Label tone={table.computed_total_acres === table.expected_total_acres ? "ok" : "mismatch"}>
                      {table.computed_total_acres === table.expected_total_acres
                        ? t("rowState.matched")
                        : t("rowState.differs")}
                    </Label>
                  </td>
                </tr>
              </tfoot>
            ) : null}
          </table>
        </div>
      )}
      {table.room_id_duplicates.length ? (
        <p className={styles.note}>
          <Label tone="manual">{t("duplicateLabel")}</Label> {t("duplicates", { ids: table.room_id_duplicates.join(", ") })}
        </p>
      ) : null}
    </>
  );
}

/** Findings that rest on a signature chain or on a lookup in the simulated registry carry the tag. */
function flagSource(flag: Flag): "simulated" | "testAnchor" | null {
  if (flag.rule_id.startsWith("SIG-")) return "testAnchor";
  if (flag.rule_id === "STAMP-REUSE" || flag.rule_id.startsWith("UDIN-REUSE")) return "simulated";
  return null;
}

export function FlagCard({ flag, t, title }: { flag: Flag; t: T; title: string }) {
  const extracted = preview(flag.extracted_value);
  const expected = preview(flag.expected_value);
  const headingId = `flag-${flag.flag_id}`;
  return (
    <article className={styles.flag} aria-labelledby={headingId}>
      <div className={styles.flagStrip}>
        <StatusLabel label={flag.label} />
        <span className={styles.label} data-tone="neutral">
          {t(`severity.${flag.severity}`)}
        </span>
        <span className={styles.provenance}>{t("provenanceSatya")}</span>
        <span className={styles.mono}>{flag.flag_id.slice(-6)}</span>
      </div>
      <div className={styles.flagBody}>
        <h3 id={headingId}>{title}</h3>
        <dl className={styles.facts}>
          <dt>{t("rule")}</dt>
          <dd className={styles.mono}>{t("ruleVersion", { id: flag.rule_id, version: flag.rule_version })}</dd>
          <dt>{t("aphClause")}</dt>
          <dd>{t("clauseEdition", { clause: flag.aph_clause, edition: flag.aph_edition })}</dd>
          <dt>{t("confidence")}</dt>
          <dd>
            {flag.confidence.toFixed(2)} · {t(`band.${flag.confidence_band}`)}
          </dd>
          <dt>{t("evidence")}</dt>
          <dd>{flag.page ? t("swornPage", { page: flag.page }) : t("none")}</dd>
          <dt>{t("swornValue")}</dt>
          <dd>{extracted === null ? <span className={styles.wrong}>{t("notFound")}</span> : <span className={styles.wrong}><Cell value={extracted} t={t} /></span>}</dd>
          <dt>{t("expectedValue")}</dt>
          <dd>
            {expected === null ? t("none") : <Cell value={expected} t={t} />}
            <span className={styles.expectedValue}>{flag.expected_source.label}</span>
            {flagSource(flag) ? (
              <>
                {" "}
                <SourceTag kind={flagSource(flag) ?? "simulated"} />
              </>
            ) : null}
          </dd>
          {flag.delta != null ? (
            <>
              <dt>{t("differenceLabel")}</dt>
              <dd className={styles.difference}>
                {flag.delta > 0 ? `+${flag.delta}` : flag.delta} {flag.value_unit ?? ""}
              </dd>
            </>
          ) : null}
        </dl>
        {flag.preliminary_indicator ? <p className={styles.prelim}>{t("preliminary")}</p> : null}
      </div>
      <div className={styles.flagFoot}>{flag.disposition ? t("dispositionRecorded") : t("dispositionPending")}</div>
    </article>
  );
}
