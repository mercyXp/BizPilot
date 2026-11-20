from typing import TypedDict


class DemoBranchSpec(TypedDict):
    code: str
    name: str
    city: str
    kind: str


class DemoBusinessSpec(TypedDict):
    slug: str
    name: str
    legal_name: str
    industry: str
    pack: str
    size_label: str
    summary: str
    employees: int
    products: int
    monthly_revenue: int
    monthly_expenses: int
    style: str
    branches: tuple[DemoBranchSpec, ...]
    categories: tuple[str, ...]


class DemoIndustrySpec(TypedDict):
    key: str
    name: str
    summary: str
    businesses: tuple[str, ...]


INDUSTRIES: tuple[DemoIndustrySpec, ...] = (
    {
        "key": "grocery",
        "name": "Grocery & Supermarket",
        "summary": "Products, POS, purchases and stock.",
        "businesses": ("mwamba", "freshmart", "zed-wholesale"),
    },
    {
        "key": "pharmacy",
        "name": "Pharmacy",
        "summary": "Medicine inventory, expiry tracking and sales.",
        "businesses": ("medplus", "chemicare"),
    },
    {
        "key": "clothing",
        "name": "Fashion & Clothing",
        "summary": "Sizes, colours, product variants and sales.",
        "businesses": ("urban-threads", "runway-zambia"),
    },
    {
        "key": "hardware",
        "name": "Hardware & Building",
        "summary": "Materials, stock, suppliers and purchasing.",
        "businesses": ("copperbelt-build", "lumumba-hardware"),
    },
    {
        "key": "restaurant",
        "name": "Restaurant",
        "summary": "Menu, orders, sales and expenses.",
        "businesses": ("nshima-house", "lakeview-grill"),
    },
    {
        "key": "electronics",
        "name": "Electronics",
        "summary": "Devices, warranties, stock and sales.",
        "businesses": ("gadget-hub", "volt-byte"),
    },
)

BUSINESSES: dict[str, DemoBusinessSpec] = {
    "mwamba": {
        "slug": "mwamba",
        "name": "Mwamba Retail Group",
        "legal_name": "Mwamba Retail Group Limited",
        "industry": "grocery",
        "pack": "grocery",
        "size_label": "Medium-sized supermarket",
        "summary": "3 branches · 15 employees · 1,250 products",
        "employees": 15,
        "products": 1250,
        "monthly_revenue": 248_650,
        "monthly_expenses": 76_420,
        "style": "grocery",
        "branches": (
            {"code": "LSK", "name": "Lusaka Central", "city": "Lusaka", "kind": "headquarters"},
            {"code": "CHE", "name": "Chelstone", "city": "Lusaka", "kind": "retail"},
            {"code": "KTW", "name": "Kitwe", "city": "Copperbelt", "kind": "retail"},
        ),
        "categories": (
            "Maize meal",
            "Cooking oil",
            "Sugar",
            "Rice",
            "Beans",
            "Kapenta",
            "Fresh produce",
            "Butchery",
            "Dairy",
            "Bakery",
            "Beverages",
            "Household",
        ),
    },
    "freshmart": {
        "slug": "freshmart",
        "name": "FreshMart Stores",
        "legal_name": "FreshMart Stores Limited",
        "industry": "grocery",
        "pack": "grocery",
        "size_label": "Growing neighbourhood grocery",
        "summary": "2 branches · 8 employees · 450 products",
        "employees": 8,
        "products": 450,
        "monthly_revenue": 86_400,
        "monthly_expenses": 31_200,
        "style": "grocery",
        "branches": (
            {"code": "KAB", "name": "Kabulonga", "city": "Lusaka", "kind": "headquarters"},
            {"code": "WOO", "name": "Woodlands", "city": "Lusaka", "kind": "retail"},
        ),
        "categories": ("Maize meal", "Cooking oil", "Fresh produce", "Dairy", "Bakery", "Soft drinks"),
    },
    "zed-wholesale": {
        "slug": "zed-wholesale",
        "name": "Zed Wholesale Supplies",
        "legal_name": "Zed Wholesale Supplies Limited",
        "industry": "grocery",
        "pack": "grocery",
        "size_label": "Wholesale and distribution",
        "summary": "2 branches · 12 employees · 900 products",
        "employees": 12,
        "products": 900,
        "monthly_revenue": 410_000,
        "monthly_expenses": 142_000,
        "style": "grocery",
        "branches": (
            {"code": "SOW", "name": "Soweto Depot", "city": "Lusaka", "kind": "headquarters"},
            {"code": "NDL", "name": "Ndola Depot", "city": "Copperbelt", "kind": "retail"},
        ),
        "categories": ("Staples", "Cooking oil", "Rice", "Sugar", "Cleaning", "Beverages"),
    },
    "medplus": {
        "slug": "medplus",
        "name": "MedPlus Pharmacy",
        "legal_name": "MedPlus Pharmacy Limited",
        "industry": "pharmacy",
        "pack": "pharmacy",
        "size_label": "Community pharmacy",
        "summary": "2 branches · 10 employees · 320 products",
        "employees": 10,
        "products": 320,
        "monthly_revenue": 94_800,
        "monthly_expenses": 38_500,
        "style": "pharmacy",
        "branches": (
            {"code": "CAV", "name": "Cairo Road", "city": "Lusaka", "kind": "headquarters"},
            {"code": "MTR", "name": "Matero", "city": "Lusaka", "kind": "retail"},
        ),
        "categories": ("Pain relief", "Cough and cold", "Vitamins", "First aid", "Personal care", "Baby"),
    },
    "chemicare": {
        "slug": "chemicare",
        "name": "ChemiCare Retail",
        "legal_name": "ChemiCare Retail Limited",
        "industry": "pharmacy",
        "pack": "pharmacy",
        "size_label": "Neighbourhood pharmacy",
        "summary": "2 branches · 6 employees · 180 products",
        "employees": 6,
        "products": 180,
        "monthly_revenue": 41_200,
        "monthly_expenses": 16_800,
        "style": "pharmacy",
        "branches": (
            {"code": "CHL", "name": "Chilanga", "city": "Lusaka", "kind": "headquarters"},
            {"code": "KAF", "name": "Kafue Road", "city": "Lusaka", "kind": "retail"},
        ),
        "categories": ("Pain relief", "Vitamins", "First aid", "Personal care"),
    },
    "urban-threads": {
        "slug": "urban-threads",
        "name": "Urban Threads",
        "legal_name": "Urban Threads Zambia Limited",
        "industry": "clothing",
        "pack": "clothing",
        "size_label": "Fashion retailer",
        "summary": "2 branches · 9 employees · 280 products",
        "employees": 9,
        "products": 280,
        "monthly_revenue": 128_400,
        "monthly_expenses": 52_000,
        "style": "clothing",
        "branches": (
            {"code": "MND", "name": "Manda Hill", "city": "Lusaka", "kind": "headquarters"},
            {"code": "LEV", "name": "Levy Junction", "city": "Lusaka", "kind": "retail"},
        ),
        "categories": ("Shirts", "Chitenge", "Dresses", "Trousers", "Shoes", "Accessories"),
    },
    "runway-zambia": {
        "slug": "runway-zambia",
        "name": "Runway Zambia",
        "legal_name": "Runway Zambia Limited",
        "industry": "clothing",
        "pack": "clothing",
        "size_label": "Boutique",
        "summary": "2 branches · 5 employees · 120 products",
        "employees": 5,
        "products": 120,
        "monthly_revenue": 54_600,
        "monthly_expenses": 21_400,
        "style": "clothing",
        "branches": (
            {"code": "ARC", "name": "Arcades", "city": "Lusaka", "kind": "headquarters"},
            {"code": "EAS", "name": "East Park", "city": "Lusaka", "kind": "retail"},
        ),
        "categories": ("Dresses", "Chitenge", "Accessories"),
    },
    "copperbelt-build": {
        "slug": "copperbelt-build",
        "name": "Copperbelt Build",
        "legal_name": "Copperbelt Build Limited",
        "industry": "hardware",
        "pack": "hardware",
        "size_label": "Building supplies",
        "summary": "2 branches · 11 employees · 400 products",
        "employees": 11,
        "products": 400,
        "monthly_revenue": 186_000,
        "monthly_expenses": 71_500,
        "style": "hardware",
        "branches": (
            {"code": "KIT", "name": "Kitwe Yard", "city": "Kitwe", "kind": "headquarters"},
            {"code": "NDB", "name": "Ndola Yard", "city": "Ndola", "kind": "retail"},
        ),
        "categories": ("Cement", "Timber", "Paint", "Plumbing", "Electrical", "Tools"),
    },
    "lumumba-hardware": {
        "slug": "lumumba-hardware",
        "name": "Lumumba Hardware",
        "legal_name": "Lumumba Hardware Limited",
        "industry": "hardware",
        "pack": "hardware",
        "size_label": "Neighbourhood hardware",
        "summary": "2 branches · 7 employees · 220 products",
        "employees": 7,
        "products": 220,
        "monthly_revenue": 62_800,
        "monthly_expenses": 24_100,
        "style": "hardware",
        "branches": (
            {"code": "LUM", "name": "Lumumba Road", "city": "Lusaka", "kind": "headquarters"},
            {"code": "CHI", "name": "Chilenje", "city": "Lusaka", "kind": "retail"},
        ),
        "categories": ("Paint", "Plumbing", "Electrical", "Tools"),
    },
    "nshima-house": {
        "slug": "nshima-house",
        "name": "Nshima House",
        "legal_name": "Nshima House Limited",
        "industry": "restaurant",
        "pack": "restaurant",
        "size_label": "Family restaurant",
        "summary": "2 branches · 14 employees · 48 menu items",
        "employees": 14,
        "products": 48,
        "monthly_revenue": 97_200,
        "monthly_expenses": 44_800,
        "style": "restaurant",
        "branches": (
            {"code": "RID", "name": "Ridgeway", "city": "Lusaka", "kind": "headquarters"},
            {"code": "KAB", "name": "Kabulonga", "city": "Lusaka", "kind": "retail"},
        ),
        "categories": ("Nshima plates", "Grills", "Relish", "Drinks", "Breakfast"),
    },
    "lakeview-grill": {
        "slug": "lakeview-grill",
        "name": "Lakeview Grill",
        "legal_name": "Lakeview Grill Limited",
        "industry": "restaurant",
        "pack": "restaurant",
        "size_label": "Casual dining",
        "summary": "2 branches · 8 employees · 32 menu items",
        "employees": 8,
        "products": 32,
        "monthly_revenue": 58_400,
        "monthly_expenses": 27_600,
        "style": "restaurant",
        "branches": (
            {"code": "SIR", "name": "Siavonga", "city": "Southern", "kind": "headquarters"},
            {"code": "LIV", "name": "Livingstone", "city": "Southern", "kind": "retail"},
        ),
        "categories": ("Grills", "Drinks", "Sides"),
    },
    "gadget-hub": {
        "slug": "gadget-hub",
        "name": "Gadget Hub",
        "legal_name": "Gadget Hub Zambia Limited",
        "industry": "electronics",
        "pack": "electronics",
        "size_label": "Consumer electronics",
        "summary": "2 branches · 10 employees · 160 products",
        "employees": 10,
        "products": 160,
        "monthly_revenue": 215_000,
        "monthly_expenses": 88_400,
        "style": "electronics",
        "branches": (
            {"code": "CAM", "name": "Cairo Mall", "city": "Lusaka", "kind": "headquarters"},
            {"code": "KIT", "name": "Kitwe Mall", "city": "Kitwe", "kind": "retail"},
        ),
        "categories": ("Phones", "TVs", "Audio", "Accessories", "Power"),
    },
    "volt-byte": {
        "slug": "volt-byte",
        "name": "Volt & Byte",
        "legal_name": "Volt and Byte Limited",
        "industry": "electronics",
        "pack": "electronics",
        "size_label": "Phones and accessories",
        "summary": "2 branches · 6 employees · 90 products",
        "employees": 6,
        "products": 90,
        "monthly_revenue": 73_500,
        "monthly_expenses": 29_200,
        "style": "electronics",
        "branches": (
            {"code": "COM", "name": "COMESA Market", "city": "Lusaka", "kind": "headquarters"},
            {"code": "KAM", "name": "Kamwala", "city": "Lusaka", "kind": "retail"},
        ),
        "categories": ("Phones", "Accessories", "Power"),
    },
}


def business_by_slug(slug: str) -> DemoBusinessSpec:
    try:
        return BUSINESSES[slug]
    except KeyError as exc:
        raise KeyError(slug) from exc


def public_centre() -> dict:
    industries = []
    for industry in INDUSTRIES:
        businesses = []
        for slug in industry["businesses"]:
            spec = BUSINESSES[slug]
            businesses.append(
                {
                    "slug": spec["slug"],
                    "name": spec["name"],
                    "size_label": spec["size_label"],
                    "summary": spec["summary"],
                    "employees": spec["employees"],
                    "products": spec["products"],
                    "branches": [
                        {
                            "code": row["code"],
                            "name": row["name"],
                            "city": row["city"],
                            "kind": row["kind"],
                            "label": (
                                f"{row['name']} · Headquarters · {row['city']}"
                                if row["kind"] == "headquarters"
                                else f"{row['name']} · Retail branch · {row['city']}"
                            ),
                        }
                        for row in spec["branches"]
                    ],
                }
            )
        industries.append(
            {
                "key": industry["key"],
                "name": industry["name"],
                "summary": industry["summary"],
                "example_available": True,
                "businesses": businesses,
            }
        )
    return {"industries": industries}
