from pathlib import Path

import pandas as pd


TARGET_REGIONS = {
    "Eastern Europe",
    "Northern Europe",
    "Northern America",
}

REQUIRED_DATA_COLUMNS = {
    "Data_Referencia",
    "Codi_Barri",
    "Nom_Barri",
    "Valor",
    "NACIONALITAT_REGIO",
    "SEXE",
}


def _get_region_codes(dictionary_file: Path) -> tuple[set[str], set[str]]:
    dimensions_df = pd.read_csv(
        dictionary_file,
        encoding="utf-8-sig",
        dtype=str,
    )
    required_columns = {
        "Desc_Dimensio",
        "Codi_Valor",
        "Desc_Valor_EN",
    }
    missing_columns = required_columns.difference(dimensions_df.columns)
    if missing_columns:
        raise ValueError(
            "The dimensions dictionary is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    nationality_regions = dimensions_df.loc[
        dimensions_df["Desc_Dimensio"].eq("NACIONALITAT_REGIO")
    ].copy()
    nationality_regions["Codi_Valor"] = (
        nationality_regions["Codi_Valor"].astype("string").str.strip()
    )
    nationality_regions["Desc_Valor_EN"] = (
        nationality_regions["Desc_Valor_EN"].astype("string").str.strip()
    )

    target_rows = nationality_regions.loc[
        nationality_regions["Desc_Valor_EN"].isin(TARGET_REGIONS)
    ]
    target_counts = target_rows["Desc_Valor_EN"].value_counts()
    if (
        set(target_rows["Desc_Valor_EN"]) != TARGET_REGIONS
        or not target_counts.eq(1).all()
    ):
        raise ValueError(
            "The dimensions dictionary must define each target "
            "nationality region exactly once."
        )

    all_region_codes = set(nationality_regions["Codi_Valor"])
    target_region_codes = set(target_rows["Codi_Valor"])
    return all_region_codes, target_region_codes


def nationality_processing(config: dict) -> pd.DataFrame:
    """
    Calcula el percentatge de població de les tres regions objectiu per barri i any.

    Els registres d'ambdós sexes es combinen. El denominador inclou tots els
    codis de regió de nacionalitat. Es conserven els grups barri-any incomplets
    amb el percentatge marcat com a NaN.
    """
    input_folder = Path(config["input_file"])
    if not input_folder.is_dir():
        raise NotADirectoryError(
            f"La carpeta de dades de nacionalitat no existeix: {input_folder}"
        )

    csv_config = config.get("csv", {})
    separator = csv_config.get("separator", ",")
    encoding = csv_config.get("encoding", "cp1252")
    null_values = {
        str(value).strip() for value in csv_config.get("null_values", ["..", ""])
    }
    dictionary_file = Path(config["dictionary_file"])

    data_files = sorted(input_folder.glob("*.csv"))
    if not data_files:
        raise FileNotFoundError(
            f"No s'han trobat fitxers CSV a la carpeta: {input_folder}"
        )

    all_region_codes, target_region_codes = _get_region_codes(dictionary_file)
    yearly_data = []

    for data_file in data_files:
        data_df = pd.read_csv(
            data_file,
            sep=separator,
            encoding=encoding,
            dtype=str,
            keep_default_na=False,
        )
        missing_columns = REQUIRED_DATA_COLUMNS.difference(data_df.columns)
        if missing_columns:
            raise ValueError(
                f"{data_file} is missing required columns: "
                f"{sorted(missing_columns)}"
            )

        dates = pd.to_datetime(data_df["Data_Referencia"], errors="coerce")
        if dates.isna().any():
            raise ValueError(
                f"{data_file} contains invalid Data_Referencia values."
            )
        data_df["Any"] = dates.dt.year
        data_df["Nom_Barri"] = data_df["Nom_Barri"].astype("string").str.strip()
        if data_df["Nom_Barri"].isna().any() or data_df["Nom_Barri"].eq("").any():
            raise ValueError(f"{data_file} contains an empty neighborhood name.")

        region_codes = data_df["NACIONALITAT_REGIO"].astype("string").str.strip()
        unknown_codes = set(region_codes).difference(all_region_codes)
        if unknown_codes:
            raise ValueError(
                f"{data_file} contains unknown nationality-region codes: "
                f"{sorted(unknown_codes)}"
            )
        data_df["NACIONALITAT_REGIO"] = region_codes

        values = data_df["Valor"].astype("string").str.strip()
        is_missing = values.isna() | values.isin(null_values)
        population = pd.to_numeric(values.mask(is_missing), errors="coerce")
        invalid_values = population.isna() & ~is_missing
        if invalid_values.any():
            invalid = sorted(values.loc[invalid_values].unique().tolist())
            raise ValueError(
                f"{data_file} contains invalid population values: {invalid}"
            )
        if population.dropna().lt(0).any():
            raise ValueError(f"{data_file} contains negative population values.")
        data_df["_population"] = population
        yearly_data.append(data_df)

    data = pd.concat(yearly_data, ignore_index=True)
    group_columns = ["Any", "Codi_Barri", "Nom_Barri"]

    row_counts = (
        data.groupby(group_columns)["_population"]
        .agg(total_rows="size", valid_rows="count")
        .reset_index()
    )
    total_population = (
        data.groupby(group_columns)["_population"]
        .sum(min_count=1)
        .reset_index()
        .rename(columns={"_population": "total_population"})
    )
    target_population = (
        data.loc[data["NACIONALITAT_REGIO"].isin(target_region_codes)]
        .groupby(group_columns)["_population"]
        .sum(min_count=1)
        .reset_index()
        .rename(columns={"_population": "target_population"})
    )

    result = row_counts.merge(total_population, on=group_columns)
    result = result.merge(target_population, on=group_columns, how="left")
    result["target_population"] = result["target_population"].fillna(0)
    is_complete = result["total_rows"].eq(result["valid_rows"])
    if result.loc[is_complete, "total_population"].le(0).any():
        raise ValueError(
            "A neighborhood-year has zero total population; "
            "its percentage cannot be calculated."
        )

    result["Valor"] = (
        result["target_population"] / result["total_population"] * 100
    ).where(is_complete)
    result = result.rename(columns={"Nom_Barri": "Barri"})
    return (
        result[["Any", "Barri", "Valor"]]
        .sort_values(["Barri", "Any"])
        .reset_index(drop=True)
    )
