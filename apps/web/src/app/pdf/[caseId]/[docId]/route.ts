// Streams a stored synthetic PDF to the PDF.js viewer. The workbench server fetches it from the
// gateway with the official's token, so the gateway's role, region and ownership checks apply.
import { apiBytes } from "@/lib/api";
import { requireRole } from "@/lib/session";

const CASE_ID = /^cas_[0-9A-HJKMNP-TV-Z]{26}$/;
const DOC_ID = /^doc_[0-9A-HJKMNP-TV-Z]{26}$/;

export async function GET(_request: Request, { params }: { params: Promise<{ caseId: string; docId: string }> }) {
  const { caseId, docId } = await params;
  if (!CASE_ID.test(caseId) || !DOC_ID.test(docId)) return new Response(null, { status: 404 });
  await requireRole("RB", `/case/${caseId}`);
  const { bytes } = await apiBytes(`/v1/cases/${caseId}/documents/${docId}/file`, `/case/${caseId}`);
  return new Response(bytes, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": 'inline; filename="document.pdf"',
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
