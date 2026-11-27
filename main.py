from pathlib import Path
import yaml
import pandas as pd

import src.data_process as data_process
import src.data_loading as data_loading

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
    
    raw_df = data_loading.load_csv(input_config)

    raw_df = data_process.utils.remove_nulls(raw_df)
    raw_df = data_process.utils.wide_to_long(raw_df)
    raw_df = data_process.utils.keep_only_neighborhoods(raw_df)

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

    raw_df = data_loading.load_csv(input_config)

    clean_df = data_process.process_obres_espai_public(raw_df)
    TP_mask = (raw_df["tipusobra"]
                .astype("string")
                .str.strip()
                .eq("Infraestructura del transport")
                .fillna(False))
    infrastructure_tp_df = data_process.process_obres_espai_public(raw_df.loc[TP_mask])

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

    raw_df = data_loading.load_csv(input_config)
    clean_df = data_process.process_parcs_jardins(raw_df)

    return clean_df, {}


PROCESSORS  = {
    "public_works": public_works_processing,
    "parks": parks_processing,
    "basic": basic_preprocessing,
    "vehicles": data_process.vehicle_processing,
    "age": data_process.age_processing,
    "studies": data_process.education_processing,
    "income": data_process.income_processing,
    "restaurants": data_process.restaurants_processing,
    "teatres": data_process.theatre_spectators_processing,
    "esport": data_process.theatre_spectators_processing,
    "hotels": data_process.hotels_processing,
    "immigracio": data_process.immigration_processing,
    "poblacio": data_process.population_processing,
    "generate_master_dataset": data_process.generate_master_dataset
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