from pathlib import Path
from io import StringIO
import pandas as pd

# Columnes requerides per al dataset d'instal·lacions esportives
REQUIRED_COLUMNS = {
    "register_id",
    "created",
    "modified",
    "addresses_neighborhood_name",
}


def sports_facilities_processing(config: dict) -> pd.DataFrame:
    """
    Calcula el nombre d'instal·lacions esportives per barri i any.

    Per cada instal·lació es genera una fila per cada any comprès entre
    les dates de creació i modificació, ambdós inclosos. Finalment, es
    compta el nombre d'instal·lacions úniques per barri i any i s'omplen
    amb 0 les combinacions barri-any sense instal·lacions.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        pd.DataFrame: Dataframe amb les columnes Barri, Any i
                      Nombre_instalacions_esportives.
    """

    # Definim la ruta d'entrada a partir de la configuració
    input_file = Path(config["input_file"])

    # Llegim el contingut del fitxer
    with open(input_file, "r", encoding="utf-16") as file:
        content = file.read()

    # Eliminem marques BOM incrustades
    content = content.replace("\ufeff", "")

    # Llegim el CSV
    df = pd.read_csv(input_file, encoding="utf-16", dtype=str, engine="python",
                     usecols=["register_id", "created", "modified",
                              "addresses_neighborhood_name"])

    # Netegem els noms de les columnes
    df.columns = df.columns.str.strip().str.replace('"', '', regex=False)

    # Comprovem que el dataframe conté les columnes requerides
    missing_columns = REQUIRED_COLUMNS.difference(df.columns)

    if missing_columns:
        raise ValueError(f"Falten les columnes requerides: "
                         f"{sorted(missing_columns)}")

    # Netegem els camps de text
    df["register_id"] = (df["register_id"].astype("string")
                                 .str.strip())
    df["addresses_neighborhood_name"] = (
        df["addresses_neighborhood_name"].astype("string").str.strip())

    # Convertim cadenes buides en valors nuls
    df[[ "register_id", "created", "modified",
         "addresses_neighborhood_name"]] = df[[
             
            "register_id", "created", "modified", 
            "addresses_neighborhood_name"]].replace("", pd.NA)

    # Eliminem duplicats generats pels atributs repetits del mateix registre
    df = df.drop_duplicates(subset=["register_id"])

    # Convertim dates a datetime
    df["created"] = pd.to_datetime(df["created"], format="mixed", utc=True)
    df["modified"] = pd.to_datetime(df["modified"], format="mixed", utc=True)

    # Eliminem registres invàlids
    invalid_rows = (
        df["register_id"].isna() | df["created"].isna()
        | df["modified"].isna() 
        | df["addresses_neighborhood_name"].isna()
        | (df["modified"].dt.year < df["created"].dt.year)
    )
    df = df.loc[~invalid_rows].copy()

    # Extraiem els anys de creació i modificació
    start_year = df["created"].dt.year
    end_year = df["modified"].dt.year

    # Generem una llista amb tots els anys de vida de la instal·lació
    df["Any"] = [list(range(start, end + 1))
                         for start, end in zip(start_year, end_year)]
    
    # Una fila per instal·lació i any
    facilities = df.explode("Any")
    facilities["Any"] = facilities["Any"].astype(int)

    # Comptem instal·lacions úniques per barri i any
    result = (facilities.groupby(["addresses_neighborhood_name", "Any"], 
                                 as_index=False,)["register_id"]
                        .nunique()
                        .rename(columns={
                                "addresses_neighborhood_name": "Barri",
                                "register_id": "Nombre_instalacions_esportives"}))

    # Generem totes les combinacions entre barris i anys disponibles
    barris = sorted(result["Barri"].dropna().unique())
    anys = range(result["Any"].min(), result["Any"].max() + 1)

    complete_index = pd.MultiIndex.from_product([barris, anys], names=["Barri", "Any"])

    # Omplim amb 0 les combinacions barri-any sense instal·lacions
    result = (result.set_index(["Barri", "Any"])
                    .reindex(complete_index, fill_value=0).reset_index())

    result["Nombre_instalacions_esportives"] = (
        result["Nombre_instalacions_esportives"].astype(int))

    # Ordenem el resultat final
    result = (result.sort_values(["Barri", "Any"]).reset_index(drop=True))

    return (result, {})
