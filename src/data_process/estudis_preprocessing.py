from pathlib import Path
import pandas as pd


# Equivalències segons el diccionari de dimensions
NO_STUDIES_CODES = {"1"}
BASIC_STUDIES_CODES = {"2", "3", "4"}
HIGHER_STUDIES_CODES = {"5"}
UNKNOWN_CODES = {"6"}

# Columnes requerides per al dataset d'estudis
REQUIRED_COLUMNS = {
    "Data_Referencia",
    "Nom_Barri",
    "Valor",
    "NIV_EDUCA_esta",
}


def education_processing(config: dict) -> pd.DataFrame:
    """
    Calcula el percentatge de població amb estudis universitaris,
    estudis superiors i sense estudis per barri i any.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe amb els percentatges per barri i any.
    """

    # Definim la ruta d'entrada a partir de la configuració
    input_folder = Path(config["input_file"])
    if not input_folder.is_dir():
        raise NotADirectoryError(
            f"La carpeta no existeix: {input_folder}"
        )

    # Obtenim la configuració del CSV
    csv_config = config.get("csv", {})
    separator = csv_config.get("separator", ",")
    encoding = csv_config.get("encoding", "cp1252")
    null_values = {
        str(value).strip()
        for value in csv_config.get("null_values", ["..", ""])
    }

    data_files = sorted(input_folder.glob("*.csv"))

    # Generem una llista per emmagatzemar els dataframes anuals
    yearly_data = []

    # Per cada fitxer CSV, llegim les dades i les processem
    for data_file in data_files:

        df = pd.read_csv(data_file, sep=separator, encoding=encoding,
                         dtype=str, keep_default_na=False)

        # Comprovem que el dataframe conté les columnes requerides
        missing_columns = REQUIRED_COLUMNS.difference(df.columns)
        if missing_columns:
            raise ValueError(
                f"{data_file} no conté les columnes requerides: "
                f"{sorted(missing_columns)}")

        # Llegim la columna de dates i extraiem l'any
        dates = pd.to_datetime(df["Data_Referencia"], errors="coerce")

        df["Any"] = dates.dt.year

        # Llegim la columna de barris i netegem els valors
        df["Nom_Barri"] = (df["Nom_Barri"].astype("string").str.strip())

        # Convertim la població a valor numèric
        population = (df["Valor"].astype("string").str.strip())
        # convertim valors nuls a NA
        population = (df["Valor"].replace(list(null_values), pd.NA))
        df["Population"] = pd.to_numeric(population, errors="coerce")

        # Guardem el dataframe anual a la llista
        yearly_data.append(df)

    # Unim tots els dataframes anuals
    data = pd.concat(yearly_data, ignore_index=True)

    # Eliminem valors sense informació
    data = data.dropna(subset=["Population"])

    # Eliminem "No consta" i agrupem per barri i any
    data = data.loc[~data["NIV_EDUCA_esta"].isin(UNKNOWN_CODES)].copy()
    group_columns = ["Any", "Nom_Barri"]

    # Població total amb nivell educatiu conegut
    total_population = (
        data.groupby(group_columns)["Population"].sum()
            .reset_index(name="Total"))
    
    #Sense estudis
    no_studies = (
    data.loc[data["NIV_EDUCA_esta"].isin(NO_STUDIES_CODES)]
        .groupby(group_columns)["Population"]
        .sum().reset_index(name="Sense_estudis"))

    # Estudis bàsics
    basic_studies = (
        data.loc[data["NIV_EDUCA_esta"].isin(BASIC_STUDIES_CODES)]
            .groupby(group_columns)["Population"]
            .sum().reset_index(name="Estudis_basics"))

    # Estudis superiors
    higher_studies = (
        data.loc[data["NIV_EDUCA_esta"].isin(HIGHER_STUDIES_CODES)]
            .groupby(group_columns)["Population"]
            .sum().reset_index(name="Estudis_superiors"))


    # Fusionem els resultats
    result = (
        total_population.merge(no_studies, on=group_columns, how="left")
                        .merge(basic_studies, on=group_columns, how="left")
                        .merge(higher_studies, on=group_columns, how="left"))

    # Omplim els valors nuls amb 0 per evitar errors en el càlcul de percentatges
    result = result.fillna(0)

    # Calculem els percentatges
    result["Sense_estudis"] = (result["Sense_estudis"]/ result["Total"]* 100)

    result["Estudis_basics"] = (result["Estudis_basics"]/ result["Total"]* 100)

    result["Estudis_superiors"] = (result["Estudis_superiors"]/ result["Total"] * 100)

    # Arreglem els noms de les columnes i retornem el dataframe final
    result = result.rename(columns={"Nom_Barri": "Barri"})[
        ["Barri","Any","Sense_estudis","Estudis_basics","Estudis_superiors"]]
    
    result = result.sort_values(["Barri", "Any"]).reset_index(drop=True)


    return (result)