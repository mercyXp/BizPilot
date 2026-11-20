export type PlanId = "basic" | "premium" | "enterprise";
export type StoreTypeId =
  | "retail"
  | "restaurant"
  | "grocery"
  | "service"
  | "pharmacy"
  | "manufacturer";

export type FeatureId =
  | "sales"
  | "returns"
  | "purchases"
  | "purchase_returns"
  | "suppliers"
  | "customers"
  | "inventory"
  | "warehouses"
  | "sections"
  | "expenses"
  | "reports"
  | "advanced_reports"
  | "assistants"
  | "shifts"
  | "ai"
  | "zra"
  | "integrations";

export const STORE_TYPES: { id: StoreTypeId; label: string }[] = [
  { id: "retail", label: "Retail Store" },
  { id: "restaurant", label: "Restaurant" },
  { id: "grocery", label: "Grocery Store" },
  { id: "service", label: "Service Provider" },
  { id: "pharmacy", label: "Pharmacy" },
  { id: "manufacturer", label: "Manufacturer" },
];

export const BILLING_COUNTRIES = [{ id: "zm", label: "Zambia (ZMW)", flag: "🇿🇲" }] as const;

const SHARED_LABELS: Record<
  Exclude<FeatureId, "inventory">,
  string
> = {
  sales: "Sales and receipts",
  returns: "Sales returns and credit notes",
  purchases: "Purchases from suppliers",
  purchase_returns: "Purchase returns",
  suppliers: "Supplier directory",
  customers: "Customers and what they owe",
  warehouses: "Storage centres, with stock moved between them",
  sections: "Store sections, with sales for each section",
  expenses: "Expense tracking",
  reports: "Business reports and analytics",
  advanced_reports: "Profit, taxation, stock movement and storage centre reports",
  assistants: "Store assistants and permissions",
  shifts: "Cashier shifts, with opening and closing cash",
  ai: "AI business assistant",
  zra: "ZRA Smart Invoice",
  integrations: "External integrations (Odoo, Manager.io, more coming)",
};

const INVENTORY_LABELS: Record<StoreTypeId, string> = {
  retail: "Products, stock levels and transfers",
  restaurant: "Menu items, stock levels and transfers",
  grocery: "Products, stock levels and transfers",
  service: "Services, stock levels and transfers",
  pharmacy: "Medications, stock levels and transfers",
  manufacturer: "Products, stock levels and transfers",
};

const FEATURE_LABELS: Record<StoreTypeId, Record<FeatureId, string>> = {
  retail: { ...SHARED_LABELS, inventory: INVENTORY_LABELS.retail },
  restaurant: { ...SHARED_LABELS, inventory: INVENTORY_LABELS.restaurant },
  grocery: { ...SHARED_LABELS, inventory: INVENTORY_LABELS.grocery },
  service: { ...SHARED_LABELS, inventory: INVENTORY_LABELS.service },
  pharmacy: { ...SHARED_LABELS, inventory: INVENTORY_LABELS.pharmacy },
  manufacturer: { ...SHARED_LABELS, inventory: INVENTORY_LABELS.manufacturer },
};

export const FEATURE_ORDER: FeatureId[] = [
  "sales",
  "returns",
  "purchases",
  "purchase_returns",
  "suppliers",
  "customers",
  "inventory",
  "warehouses",
  "sections",
  "expenses",
  "reports",
  "advanced_reports",
  "assistants",
  "shifts",
  "ai",
  "zra",
  "integrations",
];

const SERVICE_OMITTED_FEATURES: FeatureId[] = ["purchases", "purchase_returns", "suppliers"];

export const PLANS: {
  id: PlanId;
  name: string;
  monthlyKw: number;
  blurb: string;
  popular?: boolean;
  features: FeatureId[];
}[] = [
  {
    id: "basic",
    name: "Basic",
    monthlyKw: 0,
    blurb: "Core selling: sales, sales returns and expense tracking.",
    features: ["sales", "returns", "customers", "expenses"],
  },
  {
    id: "premium",
    name: "Premium",
    monthlyKw: 320,
    blurb: "Basic plus inventory, purchasing, suppliers, reports and store assistants.",
    popular: true,
    features: [
      "sales",
      "returns",
      "purchases",
      "purchase_returns",
      "suppliers",
      "customers",
      "inventory",
      "warehouses",
      "sections",
      "expenses",
      "reports",
      "assistants",
      "shifts",
    ],
  },
  {
    id: "enterprise",
    name: "Entreprise",
    monthlyKw: 490,
    blurb:
      "Everything except Manufacturing, including the AI assistant, ZRA compliance and external integrations.",
    features: [...FEATURE_ORDER],
  },
];

export const ACCOUNTING_ADDON_KW = 650;
export const PAYROLL_PER_EMPLOYEE_KW = 75;

export function featureLabel(storeType: StoreTypeId, feature: FeatureId): string {
  return FEATURE_LABELS[storeType][feature];
}

export function visibleFeatures(storeType: StoreTypeId): FeatureId[] {
  if (storeType === "service") {
    return FEATURE_ORDER.filter((feature) => !SERVICE_OMITTED_FEATURES.includes(feature));
  }
  return FEATURE_ORDER;
}

export function planIncludes(planId: PlanId, feature: FeatureId): boolean {
  const plan = PLANS.find((item) => item.id === planId);
  return plan?.features.includes(feature) ?? false;
}

export function planCardFeatures(planId: PlanId, storeType: StoreTypeId): FeatureId[] {
  return visibleFeatures(storeType).filter((feature) => planIncludes(planId, feature));
}

export function planBlurb(planId: PlanId, storeType: StoreTypeId): string {
  if (planId === "basic") {
    return "Core selling: sales, sales returns and expense tracking.";
  }
  if (planId === "premium") {
    if (storeType === "service") {
      return "Basic plus services, stock, reports and store assistants.";
    }
    if (storeType === "restaurant") {
      return "Basic plus menu items, purchasing, suppliers, reports and store assistants.";
    }
    if (storeType === "pharmacy") {
      return "Basic plus medications, purchasing, suppliers, reports and store assistants.";
    }
    return "Basic plus inventory, purchasing, suppliers, reports and store assistants.";
  }
  return "Everything except Manufacturing, including the AI assistant, ZRA compliance and external integrations.";
}

export function compareHeading(storeType: StoreTypeId): string {
  const label = STORE_TYPES.find((item) => item.id === storeType)?.label ?? "store";
  return `What a ${label.toLowerCase()} gets on each plan`;
}

export function formatKw(amount: number): string {
  if (amount === 0) {
    return "Free";
  }
  return `K${amount.toLocaleString("en-ZM")}`;
}
