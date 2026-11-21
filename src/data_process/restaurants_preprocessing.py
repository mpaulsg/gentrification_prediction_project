from pathlib import Path
import pandas as pd
from io import StringIO


# Columnes requerides per al dataset de restaurants
REQUIRED_COLUMNS = {
    "register_id",
    "created",
    "modified",
    "addresses_neighborhood_name",
}


def restaurants_processing(config: dict) -> pd.DataFrame:
    """
    Calcula el nombre de restaurants per barri i any.

    Per cada restaurant es genera una fila per cada any comprès entre
    les dates de creació i modificació (ambdós inclosos). Finalment
    es compta el nombre de restaurants per barri i any.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        pd.DataFrame: Dataframe amb les columnes
                      Barri, Any i Nombre_restaurants.
    """

    # Definim la ruta d'entrada a partir de la configuració
    input_file = Path(config["input_file"])

    # Obtenim la configuració del CSV
    csv_config = config.get("csv", {})
    separator = csv_config.get("separator", ",")
    encoding = csv_config.get("encoding", "utf-16")

    with open(input_file, "r", encoding="utf-16") as file:
        content = file.read()

    # Eliminem marques BOM incrustades
    content = content.replace("\ufeff", "")
    # Llegim el fitxer
    df = pd.read_csv(StringIO(content), sep=",", dtype=str)

    # Comprovem que el dataframe conté les columnes requerides
    missing_columns = REQUIRED_COLUMNS.difference(df.columns)

    if missing_columns:
        raise ValueError(f"Falten les columnes requerides: "
                         f"{sorted(missing_columns)}")

    # Ens quedem només amb les columnes necessàries
    restaurants = df[["register_id", "created", "modified", 
                      "addresses_neighborhood_name"]].copy()

    # Eliminem possibles duplicats del mateix restaurant
    restaurants = restaurants.drop_duplicates(subset=["register_id"])

    # Convertim dates a datetime
    restaurants["created"] = pd.to_datetime(restaurants["created"], 
                                            format="mixed", utc=True)
    restaurants["modified"] = pd.to_datetime(restaurants["modified"],
                                             format="mixed", utc=True)

    # Netegem els noms dels barris
    restaurants["addresses_neighborhood_name"] = (
        restaurants["addresses_neighborhood_name"].astype("string").str.strip())

    # Eliminem registres invàlids
    invalid_rows = (
        restaurants["created"].isna() | restaurants["modified"].isna()
        | restaurants["addresses_neighborhood_name"].isna()
        | ( restaurants["modified"].dt.year < restaurants["created"].dt.year))
    restaurants = restaurants.loc[~invalid_rows].copy()

    # Extraiem anys de creació i modificació
    start_year = restaurants["created"].dt.year
    end_year = restaurants["modified"].dt.year

    # Generem una llista amb tots els anys de vida del restaurant
    restaurants["Any"] = [list(range(start, end + 1))
                          for start, end in zip(start_year, end_year)]

    # Una fila per restaurant i any
    restaurants = restaurants.explode("Any")
    restaurants["Any"] = restaurants["Any"].astype(int)

    # Comptem restaurants per barri i any
    result = (restaurants.groupby(["addresses_neighborhood_name", "Any"],
                                  as_index=False)
                         .size()
                         .rename(columns={
                             "addresses_neighborhood_name": "Barri",
                             "size": "Nombre_restaurants",}))

    # Ordenem el resultat final
    result = (result.sort_values(["Barri", "Any"]).reset_index(drop=True))

    return (result, {})