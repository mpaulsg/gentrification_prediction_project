# master_df_generation.py

from pathlib import Path
import glob
import pandas as pd
from src.data_process.utils import keep_only_neighborhoods, normalize_neighborhood_name


def validate_columns(df, file):
    """
    Funció que garanteix que tots els datasets tenen les columnes "Any i "Barri"
    Args:
        df (pd.DataFrame): Dataframe a validar.

        file (str):Ruta o nom del fitxer d'origen. S'utilitza per generar
            missatges d'error més descriptius.

    """
    required_columns = {"Barri", "Any"}
    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"El fitxer {file} no conté les columnes obligatòries: {missing}")


def validate_duplicates(df, file):
    """
    Comprova que el dataframe conté les columnes obligatòries
    necessàries per a la generació del dataset mestre.
    Args:
        df (pd.DataFrame):Dataframe a validar.
        file (str):Ruta o nom del fitxer d'origen. 
    """

    duplicated_rows = df.duplicated(subset=["Barri", "Any"], keep="first")

    if duplicated_rows.any():

        duplicate_keys = (df.loc[duplicated_rows, ["Barri", "Any"]]
                            .drop_duplicates().to_dict("records"))

        print(f"WARNING: S'han trobat duplicats de (Barri, Any) a {file}: "
              f"{duplicate_keys[:10]}. Són eliminats.")

        df = df.drop_duplicates(subset=["Barri", "Any"],keep="first")

    return df


def load_and_merge_datasets(processed_dir):
    """
    Carrega, valida i fusiona tots els datasets preprocessats en un únic
    dataframe mestre, utilitzant les columnes "Barri" i "Any" com a claus 
    d'unió.
    Args:
        processed_dir (str): Ruta al directori amb els datasets preprocessats
    Returns:
        pd.DataFrame: Dataset final que conté tots els paràmetres
    """

    # Carreguem tots els fitxers
    csv_files = glob.glob(str(Path(processed_dir) / "**" / "*.csv"),
                          recursive=True)
    csv_files = [file for file in csv_files
                 if Path(file).name != "master_dataset.csv" ]
    if not csv_files:
        raise ValueError(f"No s'ha trobat cap CSV a {processed_dir}")

    master_df = None

    # Obrim un a un els fitxers
    for file in sorted(csv_files):

        # Carrega del fitxer i normalització del nom de les columnes Barri i Any
        print(f"Carregant {file}")
        df = pd.read_csv(file)
        df = df.rename(columns={"barri": "Barri", "any": "Any",})

        # Validació de que tenim les columnes necessàries per seguir
        validate_columns(df, file)

        # Normalització dels noms dels barris
        df["Barri"] = df["Barri"].astype(str)
        df["Any"] = pd.to_numeric(df["Any"])
        df["Barri"] = (df["Barri"].apply(normalize_neighborhood_name))

        # En el cas de les obres a l'espai públic tenim Zona Franca que pertany 
        # a la Marina del Prat Vermell, per això després de normalitzar el nom 
        # del barri en sumem els valors
        if "Obres_Espai_Public" in Path(file).stem:
            value_columns = [col for col in df.columns 
                             if col not in ["Barri", "Any"] ]
            print(f"INFO: Agrupant duplicats d'Obres_Espai_Public a {file}")

            df = (df.groupby(["Barri", "Any"],as_index=False)[value_columns]
                    .sum())

        # Eliminem les files que no tinguin un nom a la columna "Barri" que 
        # consti al fitxer base "config/Barris_Districes_Barcelona.csv"
        df = keep_only_neighborhoods(df)

        # Netegem possibles valors duplicats
        validate_duplicates(df, file)

        # Si el DataFrame general "master_df" no existeix el generem, i si ja 
        # existeix hi afegim columnes noves.
        if master_df is None:
            master_df = df
        else:
            master_df = master_df.merge(df, on=["Barri", "Any"],
                                            how="outer", validate="one_to_one")
    return master_df


def generate_master_dataset(preprocess_config):
    # Path a la carpeta amb els datasets per paràmetre
    processed_dir = preprocess_config["single_preprocessed_dir"]

    # Any inicial i final de l'anàlisi
    start_year = preprocess_config["filters"]["start_year"]
    end_year = preprocess_config["filters"]["end_year"]

    # Generació del dataset conjunt
    master_df = load_and_merge_datasets(processed_dir)

    # Filtrem el dataset final per quedar-nos amb les dades dels anys desitjats
    master_df = master_df[(master_df["Any"] >= start_year)
                            & (master_df["Any"] <= end_year)].copy()

    # Omplim els valors nuls
    master_df = master_df.fillna(0)

    # Creem una columna datetime a partir de l'any
    master_df["Any_datetime"] = pd.to_datetime(master_df["Any"]
                                               .astype(str) + "-01-01")

    master_df = (master_df.sort_values(["Barri", "Any"]).reset_index(drop=True))

    print(f"Dataset final: {len(master_df)} files, "
          f"{len(master_df.columns)} columnes")

    print("\nPercentatge de valors nuls:")
    print((master_df.isna().mean() * 100).sort_values(ascending=False)
                    .round(2))
    return master_df, {}