from pathlib import Path
import pandas as pd

# Columnes requerides per al dataset d'immigració
REQUIRED_COLUMNS = {
    "Any",
    "Nom_Barri",
    "Valor",
}


def immigration_processing(config: dict) -> pd.DataFrame:
    """
    Calcula el nombre total d'immigrants per barri i any.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe amb el nombre d'immigrants per barri i any.
    """

    # Definim la ruta d'entrada a partir de la configuració
    input_folder = Path(config["input_file"])

    data_files = sorted(input_folder.glob("*.csv"))

    # Generem una llista per emmagatzemar els dataframes anuals
    yearly_data = []

    # Per cada fitxer CSV, llegim les dades i les processem
    for data_file in data_files:

        null_values = {str(value).strip()
                        for value in config.get("null_values", ["..", ""])}

        df = pd.read_csv(data_file, encoding="utf-8", dtype=str, engine="python",
                         usecols=["Any", "Nom_Barri", "Valor"])

        # Comprovem que el dataframe conté les columnes requerides
        missing_columns = REQUIRED_COLUMNS.difference(df.columns)

        if missing_columns:
            raise ValueError(f"{data_file} no conté les columnes requerides: "
                             f"{sorted(missing_columns)}")

        # Netegem els noms dels barris
        df["Nom_Barri"] = (df["Nom_Barri"].astype("string").str.strip())

        # Convertim l'any a numèric
        df["Any"] = pd.to_numeric(df["Any"], errors="coerce")

        # Netegem i convertim el nombre d'immigrants
        immigrants = (df["Valor"].astype("string").str.strip()
                      .replace(list(null_values), pd.NA))

        df["Immigrants"] = pd.to_numeric(immigrants, errors="coerce")

        yearly_data.append(df)

    # Unim tots els dataframes anuals
    data = pd.concat(yearly_data, ignore_index=True)

    # Eliminem registres invàlids
    data = data.dropna(subset=["Nom_Barri", "Any", "Immigrants"])

    # Sumem totes les AEB i seccions censals d'un mateix barri
    grouped = (data.groupby(["Any", "Nom_Barri"], as_index=False)
                   .agg(Nombre_immigrants=("Immigrants", "sum")))

    result = grouped.rename(columns={"Nom_Barri": "Barri"}
                            )[["Barri", "Any", "Nombre_immigrants"]]

    result =  result.sort_values(["Barri", "Any"]).reset_index(drop=True)

    return (result, {})