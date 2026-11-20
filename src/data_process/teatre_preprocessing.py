from pathlib import Path
import pandas as pd


# Columnes requerides pel dataset de teatres
REQUIRED_COLUMNS = {
    "Any",
    "Indicador",
    "Valor",
    "Nom_Barri",
}


def theatre_spectators_processing(config: dict) -> pd.DataFrame:
    """
    Calcula el nombre total d'espectadors de teatre
    per barri i any.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe amb: Barri, Any i Nombre_espectadors_teatre
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
    encoding = csv_config.get("encoding", "utf-8")

    data_files = sorted(input_folder.glob("*.csv"))

    # Generem una llista per emmagatzemar els dataframes anuals
    yearly_data = []

    # Per cada fitxer CSV, llegim les dades i les processem
    for data_file in data_files:

        df = pd.read_csv(data_file, sep=separator, encoding=encoding,
                         dtype=str, keep_default_na=False )

        # Comprovem que el dataframe conté les columnes requerides
        missing_columns = REQUIRED_COLUMNS.difference(df.columns)

        if missing_columns:
            raise ValueError(f"{data_file} no conté les columnes requerides: "
                             f"{sorted(missing_columns)}")

        # Ens quedem únicament amb l'indicador d'espectadors
        df = df[df["Indicador"] == "Espectadors"].copy()

        # Netegem els noms dels barris
        df["Nom_Barri"] = (df["Nom_Barri"].astype("string").str.strip())

        # Convertim l'any a valor numèric
        df["Any"] = pd.to_numeric(df["Any"], errors="coerce")

        # Convertim el nombre d'espectadors a numèric
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")

        # Guardem el dataframe anual a la llista
        yearly_data.append(df)

    # Unim tots els dataframes anuals
    data = pd.concat(yearly_data, ignore_index=True)

    # Eliminem files amb dades no disponibles
    data = data.dropna(subset=["Any", "Nom_Barri", "Valor"])

    # Agrupem per barri i any sumant espectadors
    result = (data.groupby(["Any", "Nom_Barri"], as_index=False)
                  .agg(Nombre_espectadors_teatre=("Valor", "sum")))

    # Per les convinacions any-barri sense dades, afegim files amb valor 0
    barris = sorted(result["Nom_Barri"].dropna().unique())
    anys = sorted(result["Any"].dropna().unique())

    complete_index = pd.MultiIndex.from_product([barris, anys], 
                                                names=["Nom_Barri", "Any"])

    result = (result.set_index(["Nom_Barri", "Any"])
                    .reindex(complete_index, fill_value=0).reset_index())

    # Arreglem els noms de les columnes
    result = result.rename(columns={"Nom_Barri": "Barri"})[
                                 ["Barri", "Any", "Nombre_espectadors_teatre"]]

    result = (result.sort_values(["Barri", "Any"]).reset_index(drop=True))

    return result