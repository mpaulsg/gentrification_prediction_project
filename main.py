from pathlib import Path
import yaml
import pandas as pd

from src.data_loading.load_csv import load_csv
from src.data_process.obra_publica_processing import process_obres_espai_public
from src.data_process.parcs_jardins_preprocessing import process_parcs_jardins
from src.data_process.vehicle_preprocessing import vehicle_processing
from src.data_process.edat_preprocessing import age_processing
from src.data_process.estudis_preprocessing import education_processing
from src.data_process.renda_llar_preprocessing import income_processing
from src.data_process.restaurants_preprocessing import restaurants_processing
from src.data_process.teatre_preprocessing import theatre_spectators_processing
from src.data_process.instalacions_esport_preprocessing import sports_facilities_processing
from src.data_process.hotels_preprocessing import hotels_processing
from src.data_process import utils

# FUNCIONS INICIALS
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

def basic_preprocessing(config):
    """
    Aplica el preprocessat bàsic a un dataset brut.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe preprocessat.
    """
    # Llegim i carreguem la informació
    input_config = {**config,
                    "csv": {**config.get("csv", {}),
                            "separator": ";",
                            "encoding": "cp1252"}}
    
    raw_df = load_csv(input_config)

    raw_df = utils.remove_nulls(raw_df)
    raw_df = utils.wide_to_long(raw_df)
    raw_df = utils.keep_only_neighborhoods(raw_df)

    return raw_df, {}


def public_works_processing(config):
    """
    Processa el dataset d'obres d'espai públic, netejant-lo i retornant-lo.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe preprocessat.
    """
    input_config = {**config,
                    "csv": {**config.get("csv", {}),
                            "separator": ",",
                            "encoding": "utf-8-sig"}}

    raw_df = load_csv(input_config)

    clean_df = process_obres_espai_public(raw_df)
    TP_mask = (raw_df["tipusobra"]
                .astype("string")
                .str.strip()
                .eq("Infraestructura del transport")
                .fillna(False))
    infrastructure_tp_df = process_obres_espai_public(raw_df.loc[TP_mask])

    infrastructure_tp_df = infrastructure_tp_df.rename(
            columns={"Valor": "Nombre_obres_TP"})
    output_path = Path(config["output_file"])
    infrastructure_output_file = output_path.with_name(
            f"{output_path.stem}_Infraestructura_Transport.csv")
    
    return clean_df, {infrastructure_output_file: infrastructure_tp_df}


def parks_processing(config):
    """
    Processa el dataset de parcs i jardins, netejant-lo i retornant-lo.
    Args:
        config (dict): Configuració carregada des del YAML.
    Returns:
        df: Dataframe preprocessat.
    """
    input_config = {**config,
                    "csv": {**config.get("csv", {}),
                            "separator": ",",
                            "encoding": "utf-16",}}

    raw_df = load_csv(input_config)
    clean_df = process_parcs_jardins(raw_df)

    return clean_df, {}


PROCESSORS  = {
    "public_works": public_works_processing,
    "parks": parks_processing,
    "basic": basic_preprocessing,
    "vehicles": vehicle_processing,
    "age": age_processing,
    "studies": education_processing,
    "income": income_processing,
    "restaurants": restaurants_processing,
    "teatres": theatre_spectators_processing,
    "esport": sports_facilities_processing,
    "hotels": hotels_processing,
}


def run_preprocessing():
    """
    Funció que executa el preprocessat de dades segons la configuració especificada.
    """
    # Path a la configuració de preprocessat
    preprocess_config = load_config("src/config/preprocess_config.yaml")

    # Obtenim el nom del processador i la funció corresponent
    processor_name = preprocess_config["processor"]
    processor = PROCESSORS.get(processor_name)

    if processor is None:
        raise ValueError(f"Unknown processor: {processor_name!r}")

    # Executem el processador amb la configuració carregada
    result = processor(preprocess_config)

    print(type(result))
    print(result)
    clean_df, additional_outputs = processor(preprocess_config)

    clean_df.to_csv(preprocess_config["output_file"], index=False)

    print(f"Processed file saved to "
          f"{preprocess_config['output_file']}")

    for output_file, output_df in additional_outputs.items():
        output_df.to_csv(output_file, index=False)
        print(f"Filtered file saved to {output_file}")


def main():
    """
    Punt d'entrada principal de l'aplicació.
    """

    functionalities = {
        "1": ("Preprocessing", run_preprocessing)}

    while True:
        print("\nSelect a functionality:")

        for choice, (name, _) in functionalities.items():
            print(f"{choice}. {name}")

        print("0. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "0":
            break

        selected = functionalities.get(choice)

        if selected is None:
            print("Invalid choice. ")
            continue

        _, functionality = selected
        functionality()
        break


if __name__ == "__main__":
    main()