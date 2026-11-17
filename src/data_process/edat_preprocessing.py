from pathlib import Path
import pandas as pd

# Columnes requerides per al dataset d'edat
REQUIRED_COLUMNS = {
    "Data_Referencia",
    "Nom_Barri",
    "Valor",
    "EDAT_1",
}


def age_processing(config: dict) -> pd.DataFrame:
    """
    Calcula l'edat mitjana ponderada per població per barri i any.  
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe amb l'edat mitjana ponderada per població per barri i any.
    """
    
    # Definim la ruta d'entrada a partir de la configuració
    input_folder = Path(config["input_file"])
    if not input_folder.is_dir():
        raise NotADirectoryError(f"La carpeta no existeix: {input_folder}")

    # Obtenim la configuració del CSV a partir de la configuració
    csv_config = config.get("csv", {})
    separator = csv_config.get("separator", ",")
    encoding = csv_config.get("encoding", "cp1252")
    null_values = {str(value).strip()
                   for value in csv_config.get("null_values", ["..", ""])}

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
                f"{sorted(missing_columns)}"
            )

        # Llegim la columna de dates i extraiem l'any
        dates = pd.to_datetime(df["Data_Referencia"], errors="coerce")
        df["Any"] = dates.dt.year

        # Llegim la columna de noms de barris i netegem els valors
        df["Nom_Barri"] = (df["Nom_Barri"].astype("string").str.strip())

        # Generem una columna nova on guardem la població com a valor numèric 
        # després de netejar els valors nuls
        population = (df["Valor"].astype("string").str.strip()
                      .replace(list(null_values), pd.NA))

        # Convertim la columna de població a tipus numèric, gestionant errors
        df["Population"] = pd.to_numeric(population, errors="coerce")

        # Generem una columna nova on guardem l'edat com a valor numèric
        df["Age"] = pd.to_numeric(df["EDAT_1"], errors="coerce")

        # Guardem el dataframe processat a la llista d'anys
        yearly_data.append(df)

    # Unim tots els dataframes anuals en un únic dataframe
    data = pd.concat(yearly_data, ignore_index=True)

    # Eliminem files amb dades no disponibles
    data = data.dropna(subset=["Population", "Age"])

    # Agrupem per any i barri, calculant l'edat mitjana ponderada per població
    grouped = (
        data.assign(weighted_age=data["Population"] * data["Age"])
            .groupby(["Any", "Nom_Barri"], as_index=False)
            .agg(total_population=("Population", "sum"),
                weighted_sum=("weighted_age", "sum")))

    grouped["Valor"] = (grouped["weighted_sum"] / grouped["total_population"])

    return (
        grouped.rename(
            columns={"Nom_Barri": "Barri"}
        )[["Any", "Barri", "Valor"]]
        .sort_values(["Barri", "Any"])
        .reset_index(drop=True)
    )