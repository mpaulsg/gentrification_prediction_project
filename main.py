from pathlib import Path
import yaml
import pandas as pd

from src.data_loading.load_csv import load_csv
from src.data_process.obra_publica_processing import process_obres_espai_public
from src.data_process.parcs_jardins_preprocessing import process_parcs_jardins
from src.data_process.nacionalitat_preprocessing import nationality_processing
from src.data_process.vehicle_preprocessing import vehicle_processing
from src.data_process.edat_preprocessing import age_processing
from src.data_process.estudis_preprocessing import education_processing
from src.data_process.renda_llar_preprocessing import income_processing
from src.data_process.restaurants_preprocessing import restaurants_processing
from src.data_process.teatre_preprocessing import theatre_spectators_processing
from src.data_process.instalacions_esport_preprocessing import sports_facilities_processing
from src.data_process import utils


def _process_basic_dataset(config, raw_df):
    return basic_preprocessing(config, raw_df), {}


def _process_public_works(config, raw_df):
    """
    Processa el dataset d'obres públiques, netejant-lo i filtrant les obres
    d'infraestructura de transport per separat.
    Args:
        config (dict): Configuració carregada des del YAML.
        raw_df (pandas.DataFrame): Dataframe original carregat des del CSV.
    Returns:
        tuple: Un dataframe netejat i un diccionari amb els dataframes filtrats.
    """
    if "tipusobra" not in raw_df.columns:
        raise ValueError(
            "The public-works CSV must contain a 'tipusobra' column."
        )

    clean_df = process_obres_espai_public(raw_df)
    TP_mask = (
        raw_df["tipusobra"]
        .astype("string")
        .str.strip()
        .eq("Infraestructura del transport")
        .fillna(False)
    )
    infrastructure_tp_df = process_obres_espai_public(
        raw_df.loc[TP_mask]
    )
    infrastructure_tp_df = infrastructure_tp_df.rename(columns={"Valor": "Nombre_obres_TP"})[["Any", "Barri", "Nombre_obres_TP"]]
    output_path = Path(config["output_file"])
    infrastructure_output_file = output_path.with_name(
        f"{output_path.stem}_Infraestructura_Transport.csv"
    )

    return clean_df, {infrastructure_output_file: infrastructure_tp_df}


def _process_parks(raw_df):
    return process_parcs_jardins(raw_df), {}


SINGLE_FILE_PROCESSORS = {
    "basic": {
        "process": _process_basic_dataset,
        "csv": {},
    },
    "public_works": {
        "process": _process_public_works,
        "csv": {"separator": ",", "encoding": "utf-8-sig"},
    },
    "parks": {
        "process": _process_parks,
        "csv": {"separator": ",", "encoding": "utf-16"},
    },
}

FOLDER_PROCESSORS = {
    "vehicles": vehicle_processing,
    "nationality": nationality_processing,
    "age": age_processing,
    "studies": education_processing,
    "income": income_processing,
    "restaurants": restaurants_processing,
    "teatres": theatre_spectators_processing,
    "esport": sports_facilities_processing,
}


def load_config(config_file):
    """
    Carrega el fitxer de configuració YAML.
    Args:
        config_file (str): Ruta del fitxer YAML.
    Returns:
        dict: Diccionari amb tota la configuració del pipeline.
    """
    with open(config_file, "r", encoding="cp1252") as f:
        return yaml.safe_load(f)

def basic_preprocessing(config, df):
    """
    Aplica el preprocessat bàsic a un dataset brut.
    Args:
        config (dict): Configuració carregada des del YAML.
        df (pandas.DataFrame): Dataframe original carregat des del CSV. 
    Returns:
        df: Dataframe preprocessat.
    """

    df = utils.filter_years(
        df,
        config["filters"]["start_year"],
        config["filters"]["end_year"]
    )

    df = utils.remove_nulls(df)
    df = utils.wide_to_long(df)
    df = utils.keep_only_neighborhoods(df)

    return df


def run_preprocessing():
    """
    Despatxa el dataset al preprocessador indicat a la configuració i desa
    tots els resultats generats.
    """
    preprocess_config = load_config("src/config/preprocess_config.yaml")
    input_type = preprocess_config.get("type")
    processor_name = preprocess_config.get("processor")
    additional_outputs = {}

    if input_type == "single_file":
        processor = SINGLE_FILE_PROCESSORS.get(processor_name)
        if processor is None:
            raise ValueError(
                f"Unknown single-file processor: {processor_name!r}"
            )

        input_config = {**preprocess_config,
            "csv": {**preprocess_config.get("csv", {}), **processor["csv"]}}
        raw_df = load_csv(input_config)
        clean_df, additional_outputs = processor["process"](preprocess_config, 
                                                            raw_df)
    elif input_type == "folder":
        processor = FOLDER_PROCESSORS.get(processor_name)
        if processor is None:
            raise ValueError(f"Unknown folder processor: {processor_name!r}")
        clean_df = processor(preprocess_config)
    else:
        raise ValueError(
            f"Unsupported input type: {input_type!r}. "
            "Expected 'single_file' or 'folder'."
        )

    clean_df.to_csv(preprocess_config["output_file"], index=False)
    print(f"Processed file saved to {preprocess_config['output_file']}")
    for output_file, output_df in additional_outputs.items():
        output_df.to_csv(output_file, index=False)
        print(f"Filtered file saved to {output_file}")


def main():
    """
    Punt d'entrada principal de l'aplicació. Mostra un menú interactiu i executa
    la funcionalitat seleccionada per l'usuari. Les opcions són:

        1. Preprocessing
            Neteja i homogeneïtzació de dades.

        2. Postprocessing
            Fusió de datasets i construcció del
            dataset mestre.

        3. Clustering
            Agrupació de barris segons les
            característiques socioeconòmiques
            i urbanístiques.

    El programa finalitza després d'executar
    la funcionalitat seleccionada.
    """

    functionalities = {
        "1": ("Preprocessing", run_preprocessing),
        "2": ("Postprocessing", None),
        "3": ("Clustering", None),
    }

    while True:

        print("\nSelect a functionality:")

        #TODO: Treure el else quan estigui tot implementat
        for choice, (name, _) in functionalities.items():
            status = "" if choice == "1" else " (not implemented yet)"
            print(f"{choice}. {name}{status}")

        # Afegim l'opció de sortir del programa
        print("0. Exit")

        # Processem l'input proporcionat per l'usuari
        choice = input("Enter your choice: ").strip()

        if choice == "0":
            return

        # Missatge d'error si l'usuari introdueix una opció no vàlida
        if choice not in functionalities:
            print(
                "Invalid choice. "
                "Please select one of the listed options."
            )
            continue

        name, functionality = functionalities[choice]

        #TODO: Treure el else quan estigui tot implementat
        if functionality is None:
            print(f"{name} is not implemented yet.")
            return

        functionality()
        return


if __name__ == "__main__":
    main()