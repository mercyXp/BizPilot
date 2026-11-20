from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _split(url: str) -> tuple[str, str]:
    if "://" not in url:
        raise ValueError("Database URL must include a scheme")
    scheme, rest = url.split("://", 1)
    return scheme, rest


def with_sqlalchemy_driver(url: str, driver: str) -> str:
    _, rest = _split(url)
    return f"postgresql+{driver}://{rest}"


def as_libpq_url(url: str) -> str:
    _, rest = _split(url)
    return f"postgresql://{rest}"


def replace_user(url: str, username: str, password: str) -> str:
    parts = urlsplit(url)
    if not parts.hostname:
        raise ValueError("Database URL is missing a host")
    userinfo = f"{quote(username, safe='')}:{quote(password, safe='')}"
    host = parts.hostname
    netloc = f"{userinfo}@{host}" if parts.port is None else f"{userinfo}@{host}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def ensure_ssl(url: str, *, async_driver: bool) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host in _LOCAL_HOSTS:
        return url
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    if async_driver:
        query.setdefault("ssl", "require")
    else:
        query.setdefault("sslmode", "require")
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def owner_sync_url(database_url: str, database_url_sync: str | None) -> str:
    source = database_url_sync.strip() if database_url_sync and database_url_sync.strip() else database_url
    return ensure_ssl(with_sqlalchemy_driver(source, "psycopg"), async_driver=False)


def app_async_url(
    database_url: str,
    *,
    app_role: str | None = None,
    app_password: str | None = None,
) -> str:
    url = with_sqlalchemy_driver(database_url, "asyncpg")
    if app_role and app_password:
        url = replace_user(url, app_role, app_password)
    return ensure_ssl(url, async_driver=True)
