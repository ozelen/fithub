"""Diet calculator, reproduces the 'Раціон' spreadsheet (Адмін!B29-B38)."""

ACTIVITY_FIELDS = (
    "met",
    "protein_g_per_kg",
    "fat_g_per_kg",
    "hours_per_session",
    "times_per_week",
)


def calculate(
    *,
    sex,
    age,
    weight_kg,
    height_cm,
    body_fat_pct=None,
    target_body_fat_pct=None,
    target_weight_kg=None,
    deficit_pct=0,
    steps_per_day=0,
    activities=(),
):
    """`activities`: iterable of (met, protein_g_per_kg, fat_g_per_kg, hours_per_session, times_per_week)."""

    def r(v):
        return None if v is None else round(v, 2)

    activities = [tuple(a) for a in activities]
    lbm = weight_kg * (1 - body_fat_pct / 100) if body_fat_pct is not None else None
    if lbm is not None:
        bmr = 370 + 21.6 * lbm
    else:
        bmr = (
            10 * weight_kg + 6.25 * height_cm - 5 * age + (5 if sex == "male" else -161)
        )
    activity_kcal = sum(
        met * weight_kg * hours * times / 7 for met, _, _, hours, times in activities
    )
    tdee = 1.1 * bmr + activity_kcal + 3.2 * weight_kg * steps_per_day / 6666
    calories_in = tdee * (1 + deficit_pct / 100)
    deficit_kcal = tdee - calories_in
    warning = None
    if calories_in < 1.1 * bmr:
        warning = "Calories below 1.1 x BMR: choose a smaller deficit or add activity"

    base = lbm if lbm is not None else weight_kg
    protein_g = round(base * max([a[1] for a in activities] or [1.5]))
    fat_g = round(base * max([a[2] for a in activities] or [1.0]))
    carbs_g = round((calories_in - 4 * protein_g - 9 * fat_g) / 4)

    excess_kg = None
    if target_body_fat_pct is not None and lbm is not None:
        excess_kg = weight_kg - lbm / (1 - target_body_fat_pct / 100)
    elif target_weight_kg is not None:
        excess_kg = weight_kg - target_weight_kg
    kg_per_week = deficit_kcal * 7 / 7700 if deficit_kcal > 0 else 0
    weeks = round(excess_kg / kg_per_week) if excess_kg and kg_per_week else None

    return {
        "lbm_kg": r(lbm),
        "bmr_kcal": r(bmr),
        "activity_kcal": r(activity_kcal),
        "tdee_kcal": r(tdee),
        "deficit_kcal": r(deficit_kcal),
        "calories_in_kcal": r(calories_in),
        "protein_g": protein_g,
        "fat_g": fat_g,
        "carbs_g": carbs_g,
        "excess_kg": r(excess_kg),
        "kg_per_week": r(kg_per_week),
        "weeks": weeks,
        "warning": warning,
    }
