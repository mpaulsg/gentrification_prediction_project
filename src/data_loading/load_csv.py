from pathlib import Path
import pandas as pd


def load_csv(config: dict) -> pd.DataFrame:
    """
    Carrega un CSV segons la configuració definida al YAML i l'escriu en un 
    DataFrame.
    Args:
        config (dict): Configuració carregada des del YAML. 
    Returns:
        df: Dataframe amb les dades carregades del CSV.
    """

    # Carrega del fitxer d'input
    input_file = Path(config["input_file"])
    if not input_file.exists():
        raise FileNotFoundError(f"Fitxer no trobat: {input_file}")
    csv_config = config.get("csv", {})

    separator = csv_config.get("separator", ";")
    encoding = csv_config.get("encoding", "cp1252")
    null_values = csv_config.get( "null_values", ["-", "", "null"])

    # Generació del dataframe inicial
    df = pd.read_csv(input_file, sep=separator, encoding=encoding,
                     na_values=null_values, dtype=str)

    # Neteja general del DataFrame (eliminació de cometes i espais en blanc)
    df.columns = (df.columns.str.strip().str.replace('"', '', regex=False)
                    .str.replace("Territori", "Barri"))

    # Print de control per a l'usuari sobre el fitxer carregat i les dimensions del DataFrame
    print(f"[INFO] CSV carregat: {input_file}")
    print(f"[INFO] Files: {df.shape[0]} | Columnes: {df.shape[1]}")

    return df