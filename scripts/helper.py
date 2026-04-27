from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects import StrVector

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
