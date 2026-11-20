"""Generic chart-of-accounts template. Statutory labels are placeholders, not official rates."""

# map_key is how domain modules resolve accounts. Codes are org data after seed.
TEMPLATE: tuple[tuple[str, str, str, str, str], ...] = (
    ("1000", "Cash", "asset", "cash", "cash"),
    ("1010", "Bank", "asset", "bank", "bank"),
    ("1020", "Mobile money clearing", "asset", "clearing", "mobile_money"),
    ("1100", "Accounts receivable", "asset", "receivable", "ar"),
    ("1200", "Inventory", "asset", "inventory", "inventory"),
    ("1300", "Input tax (DEV_ONLY)", "asset", "tax", "tax_input"),
    ("2000", "Accounts payable", "liability", "payable", "ap"),
    ("2100", "Output tax (DEV_ONLY)", "liability", "tax", "tax_payable"),
    ("2200", "PAYE payable (DEV_ONLY)", "liability", "payroll", "paye"),
    ("2210", "NAPSA payable (DEV_ONLY)", "liability", "payroll", "napsa"),
    ("2220", "NHIMA payable (DEV_ONLY)", "liability", "payroll", "nhima"),
    ("2230", "Other payroll payable", "liability", "payroll", "payroll_other"),
    ("2300", "Net pay clearing", "liability", "payroll", "net_pay"),
    ("2400", "Goods received not invoiced", "liability", "accrual", "grni"),
    ("3000", "Equity", "equity", "equity", "equity"),
    ("4000", "Sales revenue", "income", "revenue", "revenue"),
    ("5000", "Cost of goods sold", "expense", "cogs", "cogs"),
    ("5100", "Salary expense", "expense", "payroll", "salary"),
    ("5200", "Employer contributions (DEV_ONLY)", "expense", "payroll", "employer"),
    ("5300", "Operating expenses", "expense", "opex", "expense"),
    ("5400", "Cash over and short", "expense", "variance", "cash_variance"),
)

COMPONENT_ACCOUNT = {
    "earning": "salary",
    "deduction": "payroll_other",
    "employer_contribution": "employer",
}

DEDUCTION_CODES = {
    "PAYE": "paye",
    "NAPSA": "napsa",
    "NHIMA": "nhima",
}
