from pathlib import Path
import pandas as pd


# Columnes requerides per al dataset de renda
REQUIRED_COLUMNS = {
    "Any",
    "Nom_Barri",
    "Import_Euros",
}


def income_processing(config: dict) -> pd.DataFrame:
    """
    Calcula la renda familiar mitjana per barri i any.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe amb la renda familiar mitjana per barri i any.
    """

    # Definim la ruta d'entrada a partir de la configuració
    input_folder = Path(config["input_file"])

    if not input_folder.is_dir():
        raise NotADirectoryError(
            f"La carpeta no existeix: {input_folder}"
        )

    data_files = sorted(input_folder.glob("*.csv"))

    # Generem una llista per emmagatzemar els dataframes anuals
    yearly_data = []

    # Per cada fitxer CSV, llegim les dades i les processem
    for data_file in data_files:

        df = pd.read_csv(data_file, encoding="utf-8", dtype=str, 
                            engine="python",
                            usecols=["Any", "Nom_Barri", "Import_Euros"])

        # Comprovem que el dataframe conté les columnes requerides
        missing_columns = REQUIRED_COLUMNS.difference(df.columns)

        if missing_columns:
            raise ValueError(
                f"{data_file} no conté les columnes requerides: "
                f"{sorted(missing_columns)}"
            )

        # Netegem els noms dels barris
        df["Nom_Barri"] = (df["Nom_Barri"].astype("string").str.strip())

        # Convertim l'any a valor numèric
        df["Any"] = pd.to_numeric(df["Any"],errors="coerce")

        # Convertim la renda a valor numèric
        df["Import_Euros"] = pd.to_numeric(df["Import_Euros"],errors="coerce")

        # Guardem el dataframe anual a la llista
        yearly_data.append(df)

    # Unim tots els dataframes anuals
    data = pd.concat(yearly_data,  ignore_index=True)

    # Eliminem files amb dades no disponibles
    data = data.dropna(subset=["Any", "Nom_Barri", "Import_Euros"])

    # Agrupem per barri i any calculant la renda mitjana
    result = (data.groupby(["Any", "Nom_Barri"], as_index=False)
                  .agg(Renda_familiar_mitjana=("Import_Euros", "mean")))

    # Arreglem els noms de les columnes
    result = result.rename(columns={"Nom_Barri": "Barri"})[
        ["Barri", "Any", "Renda_mitjana"]]

    result = (result.sort_values(["Barri", "Any"]).reset_index(drop=True))

    return (result, {})