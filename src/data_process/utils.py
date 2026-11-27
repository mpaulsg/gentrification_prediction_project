import pandas as pd


def detect_year_columns(df: pd.DataFrame) -> list:
    """
    Detecta automàticament les columnes que representen anys.
    Args:
        df (pandas.DataFrame): Dataframe a analitzar.
    Returns:        
        list: Llista de columnes que representen anys.
    """
    year_columns = []

    for col in df.columns:
        try:
            year = int(col)
            if 1900 <= year <= 2100:
                year_columns.append(col)
        except (ValueError, TypeError):
            continue
    return sorted(year_columns)


def filter_years(df: pd.DataFrame, start_year: int, end_year: int) -> pd.DataFrame:
    """
    Conserva únicament les columnes compreses entre start_year i end_year.
    Args:
        df (pandas.DataFrame): Dataframe a filtrar.
        start_year (int): Any inicial.
        end_year (int): Any final.
    Returns:
        df: Dataframe filtrat amb columnes d'anys dins del rang especific.
    """
    year_columns = detect_year_columns(df)
    selected_years = [col for col in year_columns 
                      if start_year <= int(col) <= end_year]

    non_year_columns = [col for col in df.columns if col not in year_columns]

    return df[non_year_columns + selected_years]


def remove_nulls(df: pd.DataFrame, strategy: str = "any") -> pd.DataFrame:
    """
    Elimina files amb valors nuls.

    strategy='all'
        Elimina només files amb totes les dades numèriques nul·les.

    strategy='any'
        Elimina files amb almenys un nul.

    Args:
        df (pandas.DataFrame): Dataframe a filtrar. 
        strategy (str): Estratègia per eliminar files amb valors nuls.
    Returns:
        df: Dataframe filtrat amb files amb valors nuls eliminats.  
    """
    year_columns = detect_year_columns(df)

    if strategy == "all":
        return df.dropna(subset=year_columns, how="all")

    elif strategy == "any":
        return df.dropna(subset=year_columns, how="any")

    else:
        raise ValueError("strategy ha de ser 'all' o 'any'")


def convert_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converteix columnes d'any a float.
    Args:
        df (pandas.DataFrame): Dataframe a convertir.
    Returns:
        df: Dataframe amb columnes d'any convertides a float.
    """

    year_columns = detect_year_columns(df)
    for col in year_columns:

        df[col] = (df[col].astype(str).str.replace(".", "", regex=False)
                   .str.replace(",", ".", regex=False))

        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def wide_to_long(df: pd.DataFrame, barri_column: str = "Barri") -> pd.DataFrame:
    """
    Converteix el format del DataFrame, de tenir una columna per cada any a 
    tenir una columna any, una valor, i una fila per any.

    De:
        Barri | 2016 | 2017
    a:
        Barri | Any | Valor

    Args:
        df (pandas.DataFrame): Dataframe a convertir.    
    Returns:
        df: Dataframe amb format de tres columnes.
    """

    year_columns = detect_year_columns(df)
    df = pd.melt(df, id_vars=[barri_column], value_vars=year_columns, 
                 var_name="Any", value_name="Valor")

    # Ordenem per tenir en files consecutives la informació del mateix barri 
    # per anys diferents
    df = df.sort_values(by=["Barri", "Any"]).reset_index(drop=True)

    # Fem que la columna "Valor" sigui numèrica
    df["Valor"] = (df["Valor"].astype(str)
                   .str.replace(".", "", regex=False)
                   .str.replace(",", ".", regex=False))
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")

    # Eliminem duplicats
    df = df.drop_duplicates().reset_index(drop=True)
    return df


def normalize_neighborhood_name(name: str) -> str:
    """
    Normalitza variants dels noms dels barris.
    """

    if pd.isna(name):
        return name

    name = str(name).strip()

    replacements = {
        # Normalització barri "el Poble-Sec"
        "el Poble Sec": "el Poble-Sec",
        "el Poble Sec - AEI Parc Montjuïc": "el Poble-Sec",
        "Parc de Montjuïc": "el Poble-Sec",

        # Normalització barri "la Marina del Prat Vermell"
        "la Marina del Prat Vermell - AEI Zona Franca":
            "la Marina del Prat Vermell",
        "Zona Franca":
            "la Marina del Prat Vermell",

        #Normalització barri "el Camp de l'Arpa del Clot"
        "Camp de l'Arpa del Clot":
            "el Camp de l'Arpa del Clot",

        # Normalització barri "la Vila de Gràcia"
        "Vila de Gràcia":
            "la Vila de Gràcia",

        # Normalització barri "el Barri Gòtic"
        "el Gòtic":
            "el Barri Gòtic",

        # Normalització barri "el Putxet i el Farró"
        "el Putget i Farró":
            "el Putxet i el Farró",
    }

    if name in replacements:
        name = replacements[name]

    return name


def keep_only_neighborhoods(
    df: pd.DataFrame,
    barri_column: str = "Barri",
    neighborhoods_file: str = "src/config/Barris_Districtes_Barcelona.csv") -> pd.DataFrame:

    neighborhoods_df = pd.read_csv(
        neighborhoods_file,
        encoding="utf-8"
    )

    valid_neighborhoods = set(
        neighborhoods_df["nom_barri"]
        .apply(normalize_neighborhood_name)
    )

    filtered_df = df[
        df[barri_column].isin(valid_neighborhoods)
    ].copy()

    return filtered_df