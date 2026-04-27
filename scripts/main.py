import tomli_w
import argparse
import subprocess
from helper import ANO_REF
from helper import load_auxiliar, load_uo, load_fonte
from transform import carrega_trata_dados, cria_receita_fonte_analise, cria_orcamento_analise, cria_dcmefo_analise

def build_toml():
    config = {"packages": {}}

    for year in range(ANO_REF - 3, ANO_REF + 1):
        config["packages"][f"siafi_{year}"] = {
            "path": f"https://raw.githubusercontent.com/splor-mg/dados-armazem-siafi-{year}/main/datapackage.json",
            "token": "GH_TOKEN",
            "resources": ["receita"],
        }
        if year == ANO_REF:
            config["packages"][f"reestimativa_{year}"] = {
                "path": f"https://raw.githubusercontent.com/splor-mg/dados-reestimativa-{year}/main/datapackage.json",
                "token": "GH_TOKEN",
                "resources": ["reest_rec"],
            }

    config["packages"]["dados-aux-classificadores"] = {
        "path": "https://raw.githubusercontent.com/splor-mg/dados-aux-classificadores/main/datapackage.json",
        "token": "GH_TOKEN",
        "resources": ["uo", "fonte_recurso"],
    }

    with open("data.toml", "wb") as f:
        tomli_w.dump(config, f)


def extract_command():
    try:
        subprocess.run(['dpm', 'install'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running 'dpm install': {e}")
        exit(1)
    except FileNotFoundError:
        print("Error: 'dpm' command not found. Please ensure it is installed and in your PATH.")
        exit(1)


def transform_command():
    df_auxiliar = load_auxiliar()
    df_uo = load_uo(ANO_REF)
    df_fonte_recurso = load_fonte(ANO_REF)

    valor_painel = carrega_trata_dados()

    cria_receita_fonte_analise(valor_painel=valor_painel,
                               df_auxiliar=df_auxiliar,
                               tipo_base='receita')
    cria_receita_fonte_analise(valor_painel=valor_painel,
                               df_auxiliar=df_auxiliar,
                               tipo_base='fonte')
    cria_orcamento_analise(df_auxiliar=df_auxiliar,
                           df_uo=df_uo,
                           df_fonte_recurso=df_fonte_recurso)
    cria_dcmefo_analise()


def main():
    parser = argparse.ArgumentParser(description='LDO Panel data processing tool')
    parser.add_argument('command', choices=['toml', 'extract', 'transform'],
                        help="'extract' to run dpm install, 'transform' to process data")

    args = parser.parse_args()

    if args.command == 'toml':
        build_toml()
    elif args.command == 'extract':
        extract_command()
    elif args.command == 'transform':
        transform_command()


if __name__ == '__main__':
    main()
