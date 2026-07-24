/**
 * Client-safe candidate text helpers.
 *
 * Deliberately separate from ledgerSnapshot.ts: that module reads the
 * snapshot off disk with node:fs/node:path and must stay server-only.
 * "use client" components import THIS module instead.
 */

export interface CandidateTextFields {
  rationale?: string;
  rationale_i18n?: Record<string, string>;
  risk_note?: string;
  risk_note_i18n?: Record<string, string>;
}

/** Language-aware candidate rationale: the snapshot ships tr/en/de variants. */
export function candidateRationale(c: CandidateTextFields, lang: string): string {
  return c.rationale_i18n?.[lang] ?? c.rationale ?? "";
}

/** Language-aware risk note with the same fallback rule. */
export function candidateRiskNote(c: CandidateTextFields, lang: string): string {
  return c.risk_note_i18n?.[lang] ?? c.risk_note ?? "";
}
