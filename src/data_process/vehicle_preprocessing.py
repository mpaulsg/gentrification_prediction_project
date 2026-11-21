from pathlib import Path
import pandas as pd


def vehicle_processing(config: dict) -> pd.DataFrame:
    """
    Genera un dataframe amb:
        Barri | Any | Nombre_vehicles

    Nombre_vehicles = nombre total de vehicles per barri i any.
    """
    all_years = []

    # Carrega del fitxer d'input
    input_folder = Path(config["input_file"])
    if not input_folder.exists():
        raise FileNotFoundError(f"Fitxer no trobat: {input_folder}")
    csv_config = config.get("csv", {})

    separator = csv_config.get("separator", ";")
    encoding = csv_config.get("encoding", "cp1252")
    null_values = csv_config.get( "null_values", ["-", "", "null"])
    
    # Bucle per cada fitxer de la carpeta
    for file in Path(input_folder).glob("*.csv"):

        df = pd.read_csv(file)

        # Agrupem les dades per barri i any i calculem el total
        grouped = (
            df.groupby(["Nom_Barri", "Any"], as_index=False)["Total"].sum())

        grouped = grouped.rename(columns={"Nom_Barri": "Barri", 
                                          "Total": "Nombre_vehicles"})
        all_years.append(grouped)

    # Generem el DF final
    final_df = (pd.concat(all_years, ignore_index=True)
                .sort_values(["Barri", "Any"])
                .reset_index(drop=True))

    return final_df, {}