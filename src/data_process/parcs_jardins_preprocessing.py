import pandas as pd


def process_parcs_jardins(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera un DataFrame amb el recompte acumulatiu de parcs per barri i any.
    Args:
        df (pandas.DataFrame): Dataframe amb les dades de parcs i jardins.
    Returns:
        df: Dataframe amb el recompte acumulatiu de parcs per barri i any.
    """

    # Columnes que necessitem
    required_columns = {
        "register_id",
        "created",
        "modified",
        "addresses_neighborhood_name",
    }
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError("Missing required columns")

    # Generem un DF nou només amb les columnes necessàries i netegem les dades
    parks_df = df[ ["register_id", 
                    "created", 
                    "addresses_neighborhood_name"]].copy()

    # Neteja de la columna "register_id"
    parks_df["register_id"] = (parks_df["register_id"].astype("string")
                               .str.strip().str.lstrip("\ufeff"))
    # Neteja de la columna "adresses_neighborhood_name"
    parks_df["addresses_neighborhood_name"] = (
        parks_df["addresses_neighborhood_name"].astype("string").str.strip())
    

    # Eliminem els duplicats
    parks_df = parks_df.drop_duplicates()

    # Comprovem la validesa de les dates de creació dels parcs i generem un 
    # DataFrame amb el recompte acumulatiu de parcs per barri i any.
    created_values = parks_df["created"].astype("string").str.strip()
    created_dates = pd.to_datetime(created_values, format="mixed", 
                                   errors="coerce", utc=True)
    if created_dates.isna().any():
        raise ValueError("Park creation dates must be valid.")

    # Convertim les dates a valors numèrics d'any
    created_years = pd.to_numeric(created_values.str.slice(0, 4), 
                                  errors="coerce")

    modified_values = df["modified"].astype("string").str.strip()
    modified_years = pd.to_numeric(modified_values.str.slice(0, 4), 
                                   errors="coerce")
   
    # Comprovem que cap any de creació sigui posterior a l'any de modificació
    parks_df["created_year"] = created_years.astype(int)
    latest_snapshot_year = int(modified_years.max())
    if (parks_df["created_year"] > latest_snapshot_year).any():
        raise ValueError(
            "A park creation year cannot be later than the latest "
            "modification year."
        )

    # Generem una columna nova amb una llista d'anys des de l'any de creació 
    # fins l'últim any de moficiació.
    parks_df["Any"] = [list(range(created_year, latest_snapshot_year + 1)) 
                       for created_year in parks_df["created_year"]]

    # Explodem la columna d'anys per tenir una fila per cada any de cada parc
    parks = parks_df.explode("Any")

    # Agrupem per barri i any i comptem el nombre de parcs per cada combinació
    result_df = (parks.groupby(["addresses_neighborhood_name", "Any"], 
                               as_index=False).size()
                               .rename(columns={
                                   "addresses_neighborhood_name": "Barri",
                                   "size": "Nombre_parcs"}))
    result_df["Any"] = result_df["Any"].astype(int)

    # Ordenem el DataFrame final per tenir en files consecutives la informació 
    # del mateix barri per anys diferents
    result_df = result_df[["Barri", "Any", "Nombre_parcs"]]
    result_df = result_df.sort_values(["Barri", "Any"]).reset_index(drop=True)

    return result_df