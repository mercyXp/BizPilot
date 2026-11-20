from copy import deepcopy

PACKS: tuple[dict, ...] = (
    {
        "code": "general",
        "name": "General",
        "config_schema": {"type": "object"},
        "default_modules": {"catalogue": True, "inventory": True, "sales": True},
        "default_settings": {
            "modules": {"catalogue": True, "inventory": True, "sales": True},
            "inventory": {"allow_negative_stock": False},
            "catalogue": {"track_batches": False, "track_expiry": False},
            "fiscal_year_start_month": 1,
        },
    },
    {
        "code": "grocery",
        "name": "Grocery",
        "config_schema": {"type": "object"},
        "default_modules": {"catalogue": True, "inventory": True, "sales": True},
        "default_settings": {
            "modules": {"catalogue": True, "inventory": True, "sales": True},
            "inventory": {"allow_negative_stock": False},
            "catalogue": {"track_batches": True, "track_expiry": True},
            "fiscal_year_start_month": 1,
        },
    },
    {
        "code": "pharmacy",
        "name": "Pharmacy",
        "config_schema": {
            "type": "object",
            "properties": {
                "restricted_dispense": {"type": "boolean"},
                "attribute_schema": {
                    "type": "object",
                    "properties": {
                        "generic_name": {"type": "string"},
                        "strength": {"type": "string"},
                        "restricted": {"type": "boolean"},
                    },
                },
            },
        },
        "default_modules": {"catalogue": True, "inventory": True, "sales": True},
        "default_settings": {
            "modules": {"catalogue": True, "inventory": True, "sales": True},
            "inventory": {"allow_negative_stock": False},
            "catalogue": {
                "track_batches": True,
                "track_expiry": True,
                "attribute_schema": {
                    "generic_name": {"type": "string"},
                    "strength": {"type": "string"},
                    "restricted": {"type": "boolean"},
                },
            },
            "fiscal_year_start_month": 1,
        },
    },
    {
        "code": "clothing",
        "name": "Clothing",
        "config_schema": {
            "type": "object",
            "properties": {
                "variant_axes": {"type": "array", "items": {"type": "string"}},
            },
        },
        "default_modules": {"catalogue": True, "inventory": True, "sales": True},
        "default_settings": {
            "modules": {"catalogue": True, "inventory": True, "sales": True},
            "inventory": {"allow_negative_stock": False},
            "catalogue": {
                "track_batches": False,
                "track_expiry": False,
                "variant_axes": ["size", "colour"],
            },
            "fiscal_year_start_month": 1,
        },
    },
)


def default_settings_for(pack: dict) -> dict:
    return deepcopy(pack["default_settings"])
