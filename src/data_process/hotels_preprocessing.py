from pathlib import Path
from io import StringIO
import pandas as pd

# Columnes requerides per al dataset d'hotels
REQUIRED_COLUMNS = {
    "register_id",
    "created",
    "modified",
    "addresses_neighborhood_name",
}

def hotels_processing(config: dict) -> pd.DataFrame:
    """
    Calcula el nombre d'hotels per barri i any.

    Per cada hotel es genera una fila per cada any comprès entre
    les dates de creació i modificació (ambdós inclosos).
    Finalment es compta el nombre d'hotels per barri i any.

    Args:
        config (dict): Configuració carregada des del YAML.

    Returns:
        pd.DataFrame: Dataframe amb les columnes
                      Barri, Any i Nombre_hotels.
    """

    # Definim la ruta d'entrada a partir de la configuració
    input_file = Path(config["input_file"])

    with open(input_file, "r", encoding="utf-16") as file:
        content = file.read()

    # Eliminem possibles marques BOM incrustades
    content = content.replace("\ufeff", "")

    # Llegim el fitxer
    hotels = pd.read_csv(input_file, encoding="utf-16", dtype=str, 
                         engine="python",
                         usecols=["register_id", "created", "modified", 
                                  "addresses_neighborhood_name"])

    # Netegem noms de columnes
    hotels.columns = ( hotels.columns.str.strip().str.replace('"', '', 
                                                              regex=False))

    # Comprovem que el dataframe conté les columnes requerides
    missing_columns = REQUIRED_COLUMNS.difference(hotels)

    if missing_columns:
        raise ValueError(f"Falten les columnes requerides: "
                         f"{sorted(missing_columns)}")

    # Eliminem possibles duplicats del mateix hotel
    hotels = hotels.drop_duplicates(subset=["register_id"])

    # Convertim dates a datetime
    hotels["created"] = pd.to_datetime(hotels["created"], 
                                       format="mixed", utc=True)
    hotels["modified"] = pd.to_datetime(hotels["modified"],
                                        format="mixed", utc=True)

    # Netegem els noms dels barris
    hotels["addresses_neighborhood_name"] = (
        hotels["addresses_neighborhood_name"].astype("string").str.strip())

    # Eliminem registres invàlids
    invalid_rows = (
        hotels["created"].isna()
        | hotels["modified"].isna()
        | hotels["addresses_neighborhood_name"].isna()
        | (hotels["modified"].dt.year < hotels["created"].dt.year))
    hotels = hotels.loc[~invalid_rows].copy()

    # Extraiem anys de creació i modificació
    start_year = hotels["created"].dt.year
    end_year = hotels["modified"].dt.year

    # Generem la llista d'anys de vida de cada hotel
    hotels["Any"] = [list(range(start, end + 1))
                     for start, end in zip(start_year, end_year)]

    # Una fila per hotel i any
    hotels = hotels.explode("Any")
    hotels["Any"] = hotels["Any"].astype(int)

    # Comptem hotels per barri i any
    result = (hotels.groupby(["addresses_neighborhood_name", "Any",], 
                             as_index=False)
                    .size()
                    .rename(columns={
                            "addresses_neighborhood_name": "Barri",
                            "size": "Nombre_hotels"}))

    # Generem combinacions barri-any inexistents
    barris = sorted(result["Barri"].dropna().unique())

    anys = range(result["Any"].min(), result["Any"].max() + 1)

    complete_index = pd.MultiIndex.from_product(
                                        [barris, anys], names=["Barri", "Any"])

    result = ( result.set_index(["Barri", "Any"])
                     .reindex(complete_index, fill_value=0).reset_index())

    # Ordenem el resultat final
    result = (result.sort_values(["Barri", "Any"]).reset_index(drop=True))

    return (result, {})