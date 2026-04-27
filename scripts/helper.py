import pandas as pd
from datetime import datetime, date
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects import StrVector

ANO_REF = datetime.now().year
ANO_REF_LDO = ANO_REF + 1
DATA = date.today()

def load_auxiliar():
    return pd.read_csv(
        'datapackages/tabelas_auxiliares/tab_auxiliar_fte_dcmefo.csv',
        sep=';',
        encoding='latin1',
        dtype={'CD_FONTE': 'string'},
        usecols=['CD_FONTE', 'Analise DCMEFO']
    )


def load_uo(ANO_REF):
    df = pd.read_csv(
        'datapackages/dados-aux-classificadores/data/uo.csv',
        sep=',',
        encoding='utf-8',
        dtype={'uo_cod': 'string', 'ano': 'string'}
    )
    return df[df['ano'].str.strip() == str(ANO_REF)]


def load_fonte(ANO_REF):
    df = pd.read_csv(
        'datapackages/dados-aux-classificadores/data/fonte_recurso.csv',
        sep=',',
        encoding='utf-8',
        dtype={'fonte_cod': 'string', 'ano': 'string'}
    )
    return df[df['ano'].str.strip() == str(ANO_REF)]


# Activate the automatic conversion between R data frames and pandas DataFrames
pandas2ri.activate()
base = importr('base')
relatorios = importr('relatorios')

def is_convenios_rec(base_analise):
    base_analise_relatorios =  base_analise.rename(columns={'ano': 'ANO', 'receita_cod': 'RECEITA_COD'})
    base_analise_rpy = pandas2ri.py2rpy(base_analise_relatorios)

    result = relatorios.is_convenios_rec(base_analise_rpy)
    result_pd = pandas2ri.rpy2py(result).astype(bool)

    return result_pd


def is_intra_saude_rec(base_analise):
    base_analise_relatorios =  base_analise.rename(columns={'ano': 'ANO', 'receita_cod': 'RECEITA_COD'})
    base_analise_rpy = pandas2ri.py2rpy(base_analise_relatorios)


    result = relatorios.is_intra_saude_rec(base_analise_rpy)
    result_pd = pandas2ri.rpy2py(result).astype(bool)
    return result_pd


def adiciona_desc(base_analise, target_columns=['RECEITA_COD', 'UO_COD', 'FONTE_COD'], overwrite=True):
    base_analise_relatorios =  base_analise.rename(
        columns={'ano': 'ANO',
                'receita_cod': 'RECEITA_COD',
                'uo_cod': 'UO_COD',
                'fonte_cod': 'FONTE_COD'})

    base_analise_rpy = pandas2ri.py2rpy(base_analise_relatorios)
    target_columns_rpy = StrVector(target_columns)

    result = relatorios.adiciona_desc(base=base_analise_rpy,
                                      columns = target_columns_rpy,
                                      overwrite=overwrite)

    result_pd = pandas2ri.rpy2py(result)

    return result_pd
