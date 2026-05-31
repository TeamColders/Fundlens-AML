/** Parse STR section bodies from full_report_text when API fields are empty. */

function sectionBody(fullText: string, header: string): string {
  const re = new RegExp(
    `(?:^|\\n)\\s*#*\\s*${header}\\s*:?\\s*\\n([\\s\\S]*?)(?=\\n\\s*#*\\s*(?:NARRATIVE|RECOMMENDED ACTION|REGULATORY BASIS|CASE REF|TYPOLOGY|FIU-IND)|$)`,
    'i',
  );
  const m = fullText.match(re);
  return m?.[1]?.trim() || '';
}

export function enrichStrReport<T extends {
  english_narrative?: string;
  recommended_action?: string;
  regulatory_basis?: string;
  full_report_text?: string;
}>(report: T): T {
  const full = report.full_report_text || '';
  if (!full) return report;

  return {
    ...report,
    english_narrative:
      report.english_narrative?.trim() || sectionBody(full, 'NARRATIVE'),
    recommended_action:
      report.recommended_action?.trim() || sectionBody(full, 'RECOMMENDED ACTION'),
    regulatory_basis:
      report.regulatory_basis?.trim() || sectionBody(full, 'REGULATORY BASIS'),
  };
}
