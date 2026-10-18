"""Load Open Food Facts into facts_product.

Default: apply the daily JSONL deltas not yet recorded in ImportRun (OFF keeps 14 days; they carry
full product documents, schema 1004, nutrition under `nutrition.aggregated_set`).
--full: replace the table from the nightly Parquet export (catches deletions; run monthly).
--taxonomy: (re)load facts_category from the OFF categories taxonomy.
"""

import csv
import gzip
import io
import json
import re
import tempfile
import unicodedata
import urllib.request
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from facts.models import NUTRIENTS, Category, ImportRun, Product

DELTA_BASE = "https://static.openfoodfacts.org/data/delta/"
PARQUET = "hf://datasets/openfoodfacts/product-database/food.parquet"
TAXONOMY = "https://raw.githubusercontent.com/openfoodfacts/openfoodfacts-server/main/taxonomies/food/categories.txt"
OFF_NAME = {"energy_kcal": "energy-kcal", "saturated_fat": "saturated-fat"}
COLUMNS = (
    "code", "name", "brands", "quantity", "serving_size", "serving_quantity", "stores_tags", "countries_tags",
    "categories_tags", "nutriscore_grade", "completeness", "obsolete", "last_modified_t", "per", *NUTRIENTS,
)  # fmt: skip
COLS = ", ".join(COLUMNS)
UPSERT = (
    f"INSERT INTO facts_product ({COLS}) SELECT {COLS} FROM facts_product_tmp "
    f"ON CONFLICT (code) DO UPDATE SET {', '.join(f'{c} = excluded.{c}' for c in COLUMNS if c != 'code')} "
    "WHERE excluded.last_modified_t >= facts_product.last_modified_t"
)


def _float(v):
    try:
        return None if v is None or v == "" else float(v)
    except (TypeError, ValueError):
        return None


def _text(v, limit):
    return ("" if v is None else str(v)).strip()[:limit]


def parse_product(doc):
    """Delta document -> row dict, or None when there is no barcode."""
    code = _text(doc.get("code"), 64)
    if not code:
        return None
    agg = (doc.get("nutrition") or {}).get("aggregated_set") or {}
    nutrients = agg.get("nutrients") or {}
    legacy = doc.get("nutriments") or {}
    per = agg.get("per") or ("100g" if legacy else "")
    row = {
        "code": code,
        "name": _text(doc.get("product_name"), 512),
        "brands": _text(doc.get("brands"), 512),
        "quantity": _text(doc.get("quantity"), 128),
        "serving_size": _text(doc.get("serving_size"), 128),
        "serving_quantity": _float(doc.get("serving_quantity")),
        "stores_tags": doc.get("stores_tags") or [],
        "countries_tags": doc.get("countries_tags") or [],
        "categories_tags": doc.get("categories_tags") or [],
        "nutriscore_grade": _text(doc.get("nutriscore_grade") or doc.get("nutrition_grades"), 16),
        "completeness": _float(doc.get("completeness")) or 0.0,
        "obsolete": str(doc.get("obsolete") or "").lower() in ("on", "true", "1"),
        "last_modified_t": int(doc.get("last_modified_t") or 0),
        "per": per if per in ("100g", "100ml") else "",
    }
    for col in NUTRIENTS:
        off = OFF_NAME.get(col, col)
        value = (nutrients.get(off) or {}).get("value")
        if value is None:
            value = legacy.get(f"{off}_100g")
        row[col] = _float(value) if row["per"] else None
    return row


def pg_array(items):
    return "{" + ",".join('"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"' for s in items) + "}"


def _cell(v):
    if v is None:
        return "\\N"  # explicit NULL marker so empty strings stay empty strings
    if isinstance(v, bool):
        return "t" if v else "f"
    if isinstance(v, list):
        return pg_array(v)
    return v


def copy_rows(cur, table, rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow([_cell(row[c]) for c in COLUMNS])
    buf.seek(0)
    cur.copy_expert(f"COPY {table} ({COLS}) FROM STDIN WITH (FORMAT csv, NULL '\\N')", buf)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": settings.OFF_USER_AGENT})
    return urllib.request.urlopen(req, timeout=600)


def slug(name):
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def canon(ref):
    lang, _, name = ref.partition(":")
    return f"{lang.strip()}:{slug(name)}"


def parse_taxonomy(text):
    """categories.txt -> {tag: (parents, names)}. Blocks are blank-line separated; `< lang:Parent`, `lang: Name, Synonym`."""
    out, parents, names = {}, [], {}

    def flush():
        if names.get("en"):
            out["en:" + slug(names["en"][0])] = (list(parents), {lang: n[0] for lang, n in names.items()})

    for line in text.splitlines():
        line = line.strip()
        if not line:
            flush()
            parents, names = [], {}
        elif line.startswith("<"):
            parents.append(canon(line[1:].strip()))
        elif (m := re.match(r"^([a-z]{2,3}(?:-[A-Za-z]+)?):\s*(.+)$", line)):
            names.setdefault(m.group(1), [s.strip() for s in m.group(2).split(",") if s.strip()])
    flush()
    return out


class Command(BaseCommand):
    help = "Load Open Food Facts products: daily deltas by default, --full for the Parquet snapshot, --taxonomy for categories."

    def add_arguments(self, parser):
        parser.add_argument("--full", action="store_true", help="Replace facts_product from the nightly Parquet export")
        parser.add_argument("--file", help="Apply one local delta .json.gz instead of downloading (testing)")
        parser.add_argument("--limit", type=int, default=0, help="Row cap for --full (smoke tests)")
        parser.add_argument("--taxonomy", action="store_true", help="Reload facts_category from the OFF taxonomy")
        parser.add_argument("--no-refresh", action="store_true", help="Skip the category medians refresh")

    def handle(self, *args, **opts):
        if opts["taxonomy"]:
            self.load_taxonomy()
        if opts["full"]:
            self.load_parquet(opts["limit"])
        elif opts["file"]:
            with gzip.open(opts["file"], "rt", encoding="utf-8") as fh:
                self.apply_delta(opts["file"].rsplit("/", 1)[-1], fh)
        elif not opts["taxonomy"]:
            self.apply_pending_deltas()
        if not opts["no_refresh"]:
            with connection.cursor() as cur:
                cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY facts_category_nutrition")
            self.stdout.write("refreshed facts_category_nutrition")

    def apply_pending_deltas(self):
        with fetch(DELTA_BASE + "index.txt") as resp:
            names = [n.strip() for n in resp.read().decode().splitlines() if n.strip()]
        done = set(ImportRun.objects.filter(kind="delta").values_list("name", flat=True))
        pending = [n for n in reversed(names) if n not in done]  # index is newest first; apply oldest first
        self.stdout.write(f"{len(pending)} delta file(s) to apply")
        for name in pending:
            with fetch(DELTA_BASE + name) as resp, gzip.open(resp, "rt", encoding="utf-8") as fh:
                self.apply_delta(name, fh)

    def apply_delta(self, name, lines):
        rows = {}
        for line in lines:
            if line.strip():
                row = parse_product(json.loads(line))
                if row and row["last_modified_t"] >= rows.get(row["code"], row)["last_modified_t"]:
                    rows[row["code"]] = row
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute("CREATE TEMP TABLE facts_product_tmp (LIKE facts_product) ON COMMIT DROP")
            copy_rows(cur, "facts_product_tmp", rows.values())
            cur.execute(UPSERT)
            ImportRun.objects.create(name=name, kind="delta", rows=len(rows))
        self.stdout.write(f"applied {name}: {len(rows)} products")

    def load_parquet(self, limit):
        import duckdb

        def pg_list(col):  # DuckDB list -> Postgres array literal
            return f"""'{{' || array_to_string(list_transform(coalesce({col}, []), x -> '"' || replace(replace(x, '\\', '\\\\'), '"', '\\"') || '"'), ',') || '}}'"""

        def nutrient(col):
            return f"""list_extract(list_filter(nutriments, x -> x.name = '{OFF_NAME.get(col, col)}'), 1)."100g" AS {col}"""

        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs; SET memory_limit = '1GB'; SET threads = 2")
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            path = tmp.name
        con.execute(
            f"""COPY (
              SELECT code,
                coalesce(list_extract(list_filter(product_name, x -> x.lang = 'main'), 1).text,
                         list_extract(product_name, 1).text, '')[1:512] AS name,
                coalesce(brands, '')[1:512] AS brands, coalesce(quantity, '')[1:128] AS quantity,
                coalesce(serving_size, '')[1:128] AS serving_size, try_cast(serving_quantity AS DOUBLE) AS serving_quantity,
                {pg_list('stores_tags')} AS stores_tags, {pg_list('countries_tags')} AS countries_tags,
                {pg_list('categories_tags')} AS categories_tags,
                coalesce(nutriscore_grade, '')[1:16] AS nutriscore_grade, coalesce(completeness, 0) AS completeness,
                coalesce(obsolete, false) AS obsolete, coalesce(last_modified_t, 0) AS last_modified_t,
                '100g' AS per,
                {', '.join(nutrient(c) for c in NUTRIENTS)}
              FROM read_parquet('{PARQUET}')
              WHERE code IS NOT NULL AND code <> ''
              {f'LIMIT {int(limit)}' if limit else ''}
            ) TO '{path}' (FORMAT csv, HEADER false, NULLSTR '\\N')"""
        )
        with transaction.atomic(), connection.cursor() as cur, open(path, encoding="utf-8") as fh:
            cur.execute("TRUNCATE facts_product")
            cur.copy_expert(f"COPY facts_product ({COLS}) FROM STDIN WITH (FORMAT csv, NULL '\\N')", fh)
            n = Product.objects.count()
            ImportRun.objects.create(name=f"food.parquet {date.today().isoformat()}", kind="full", rows=n)
        self.stdout.write(f"loaded {n} products from the Parquet export")

    def load_taxonomy(self):
        with fetch(TAXONOMY) as resp:
            cats = parse_taxonomy(resp.read().decode("utf-8"))
        with transaction.atomic():
            Category.objects.all().delete()
            Category.objects.bulk_create(
                [Category(tag=t, parents=p, names=n) for t, (p, n) in cats.items()], batch_size=2000
            )
            ImportRun.objects.update_or_create(name="categories.txt", kind="taxonomy", defaults={"rows": len(cats)})
        self.stdout.write(f"loaded {len(cats)} categories")
