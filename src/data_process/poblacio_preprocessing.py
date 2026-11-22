from pathlib import Path
import pandas as pd

# Columnes requerides per al dataset de població
REQUIRED_COLUMNS = {
    "Data_Referencia",
    "Nom_Barri",
    "Valor",
}


def population_processing(config: dict) -> pd.DataFrame:
    """
    Calcula la població total per barri i any.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe amb la població total per barri i any.
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
            usecols=["Data_Referencia",  "Nom_Barri", "Valor"])

        # Comprovem que el dataframe conté les columnes requerides
        missing_columns = REQUIRED_COLUMNS.difference(df.columns)

        if missing_columns:
            raise ValueError(f"{data_file} no conté les columnes requerides: "
                             f"{sorted(missing_columns)}")

        # Extraiem l'any
        dates = pd.to_datetime(df["Data_Referencia"], errors="coerce")

        df["Any"] = dates.dt.year

        # Netegem els noms dels barris
        df["Nom_Barri"] = (df["Nom_Barri"].astype("string").str.strip())

        # Convertim la població a numèric
        population = (df["Valor"].astype("string").str.strip()
                                 .replace(list(null_values), pd.NA))

        df["Population"] = pd.to_numeric(population, errors="coerce")

        yearly_data.append(df)

    # Unim tots els fitxers anuals
    data = pd.concat(yearly_data, ignore_index=True)

    # Eliminem registres invàlids
    data = data.dropna(subset=["Nom_Barri", "Any", "Population"])

    # Sumem totes les AEB, seccions censals i sexes
    grouped = (data.groupby(["Nom_Barri", "Any"], as_index=False)
                   .agg(Nombre_habitants=("Population", "sum")))
    
    result = grouped.rename(columns={"Nom_Barri": "Barri"})[[
                                     "Barri", "Any", "Nombre_habitants"]]
    
    result = result.sort_values(["Barri", "Any"], kind="stable").reset_index(drop=True)
                
    return (result, {})