import pandas as pd


def process_obres_espai_public(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocessa el dataset d'obres d'espai públic, generant un DataFrame amb
    el nombre d'obres per barri i any.
    Args:
        df (pandas.DataFrame): Dataframe original carregat des del CSV.
    Returns:
        df: Dataframe amb el nombre d'obres per barri i any.
    """
    
    # Definim les columnes del DF que ens interessen i comprovem que existeixen
    required_columns = {"nom_barri", "data_inici", "data_fi"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        raise ValueError("Missing required columns")

    # Columnes d'interès per al processament
    columns = ["nom_barri", "data_inici", "data_fi"]

    # Neteja i filtrat de dades invalides del nom del barri i de les dates
    works_df = df[columns].copy()
    works_df["nom_barri"] = works_df["nom_barri"].astype("string").str.strip()
    works_df = works_df[
        works_df["nom_barri"].notna() & works_df["nom_barri"].ne("")].copy()

    works_df["data_inici"] = pd.to_datetime(works_df["data_inici"],
                                            errors="coerce")
    works_df["data_fi"] = pd.to_datetime(works_df["data_fi"], errors="coerce")

    # Comprovació de valors nuls i rangs de dates invàlids
    invalid_dates = (works_df["data_inici"].isna() 
                     | works_df["data_fi"].isna()
                     | (works_df["data_fi"] < works_df["data_inici"]))
    # Ens quedem només amb les files amb dates vàlides
    works_df = works_df.loc[~invalid_dates].copy()

    # Generem una columna nova que llista tots els anys entre la data d'inici i
    # la data de fi de cada obra
    works_df["Any"] = [list(range(start.year, end.year + 1)) for start, end in 
                       zip(works_df["data_inici"], works_df["data_fi"])]
    # Explosió de la columna "Any" per obtenir una fila per cada any d'una obra
    works_df = works_df.explode("Any")

    # Agrupació per barri i any per obtenir el nombre d'obres per barri i any
    obres_df = (works_df.groupby(["nom_barri", "Any"], as_index=False)
                .size().rename(columns={"nom_barri": "Barri", "size": "Valor"}))
    obres_df["Any"] = obres_df["Any"].astype(int)

    # Reordenació de columnes i files per tenir un DataFrame amb format final
    obres_df = (obres_df[["Barri", "Any", "Valor"]]
                .sort_values(["Barri", "Any"]).reset_index(drop=True))
    
    return obres_df
    