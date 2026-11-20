export type MessageCatalog = {
  locale: string;
  messages: Record<string, string>;
  provenance: Record<string, string>;
  professional_keys: string[];
};

export const fallbackMessages: Record<string, string> = {
  "nav.dashboard": "Dashboard",
  "nav.reports": "Reports",
  "nav.settings": "Settings",
  "reports.title": "Reports",
  "reports.description": "Generate and download business reports",
  "reports.download": "Download CSV",
  "reports.empty": "No rows in this period.",
  "reports.forbidden": "You do not have permission to view reports.",
  "reports.tax_disclaimer": "DEV_ONLY placeholder. Not an official ZRA filing.",
  "dashboard.monthly_revenue": "Monthly revenue",
  "dashboard.profit": "Profit",
  "dashboard.expenses": "Expenses",
  "dashboard.catalogue": "Catalogue",
  "settings.language": "Language",
  "settings.language_hint":
    "Store default locale. Professional translations are marked and not overwritten by system seeds.",
  "common.save": "Save",
};

export function translate(
  messages: Record<string, string>,
  key: string,
  vars?: Record<string, string | number>,
): string {
  let value = messages[key] ?? fallbackMessages[key] ?? key;
  if (vars) {
    for (const [name, replacement] of Object.entries(vars)) {
      value = value.replaceAll(`{${name}}`, String(replacement));
    }
  }
  return value;
}
