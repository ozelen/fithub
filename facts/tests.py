from facts.management.commands.import_openfoodfacts import parse_product, parse_taxonomy, pg_array


def test_parse_product_reads_aggregated_set():
    doc = {
        "code": " 8414807516336 ",
        "product_name": "Arroz basmati",
        "brands": "Consum",
        "countries_tags": ["en:spain"],
        "categories_tags": ["en:basmati-rices"],
        "completeness": 0.8,
        "last_modified_t": 1792304438,
        "nutriments": {},
        "nutrition": {
            "aggregated_set": {
                "per": "100g",
                "nutrients": {"energy-kcal": {"value": 350}, "proteins": {"value": 8.1}, "saturated-fat": {"value": 0.2}},
            }
        },
    }
    row = parse_product(doc)
    assert row["code"] == "8414807516336"
    assert row["energy_kcal"] == 350 and row["proteins"] == 8.1 and row["saturated_fat"] == 0.2
    assert row["fat"] is None and row["per"] == "100g" and row["obsolete"] is False


def test_parse_product_falls_back_to_legacy_nutriments_and_skips_serving_only():
    legacy = parse_product({"code": "1", "nutriments": {"energy-kcal_100g": "120", "fat_100g": 3}})
    assert legacy["per"] == "100g" and legacy["energy_kcal"] == 120.0 and legacy["fat"] == 3.0
    serving = parse_product({"code": "2", "nutrition": {"aggregated_set": {"per": "serving", "nutrients": {"fat": {"value": 9}}}}})
    assert serving["per"] == "" and serving["fat"] is None
    assert parse_product({"product_name": "no barcode"}) is None


def test_parse_taxonomy_builds_tags_parents_and_names():
    text = """# comment
< en:Rices
< en:Long grain rices
en: Basmati rices, Basmati rice
es: Arroces Basmati, Arroz Basmati
fr: Riz Basmati

synonyms:en: pasta, pastas

< en:Cereals and potatoes
en: Rices
"""
    cats = parse_taxonomy(text)
    assert cats["en:basmati-rices"] == (["en:rices", "en:long-grain-rices"], {"en": "Basmati rices", "es": "Arroces Basmati", "fr": "Riz Basmati"})
    assert cats["en:rices"][0] == ["en:cereals-and-potatoes"]


def test_pg_array_quotes_every_element():
    assert pg_array(["en:spain", 'odd "name", here']) == '{"en:spain","odd \\"name\\", here"}'
