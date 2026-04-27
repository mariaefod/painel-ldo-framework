from helper import is_convenios_rec, is_intra_saude_rec, adiciona_desc
from helper import ANO_REF, ANO_REF_LDO
from frictionless import Package
import unicodedata
import pandas as pd
import numpy as np
import os
import warnings

warnings.filterwarnings('ignore')

fontes_convenios = list(range(1, 10)) + [16, 17, 24, 36, 37, 56, 57] + \
    list(range(62, 71)) + [73, 74, 92, 93, 97, 98]

ALERT_MAP = {"OK": "🟢",
             "RECEITA A SER INFORMADA PELA DCGCE/SEPLAG": "🟣",
             "ATENCAO": "🟠",
             "VALOR DISCREPANTE": "⚠️",
             "RECEITA NAO ESTIMADA": "🔴",
             "RECEITA DE REPASSE DO FES E LANCADA PELA SPLOR": "🔵",
             "RECEITA DE CONVENIOS EM FONTE NAO ESPERADA": "🟤"}


def get_alert_icon(alert_text):
    if pd.isna(alert_text):
        return "📌"

    texto = str(alert_text).upper().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    return ALERT_MAP.get(texto, "📌")


def build_df(datapackage, columns_to_use):
    package = Package(f'datapackages/{datapackage}/datapackage.json')
    resource = package.get_resource(package.resource_names[0])
    df = resource.to_pandas()
    df = df[columns_to_use]
    if datapackage.endswith(str(ANO_REF)):
        df['ano'] = datapackage
    return df


def carrega_trata_dados():
    siafi_columns_to_use = ['ano', 'uo_cod', 'receita_cod', 'fonte_cod', 'receita_cod_formatado',
                            'vlr_previsto_inicial', 'vlr_efetivado_ajustado']

    siafi_dfs = []
    for year in range(ANO_REF, ANO_REF - 4, -1):
        siafi_df = build_df(f'siafi_{year}', siafi_columns_to_use)
        siafi_dfs.append(siafi_df)
    siafi_df = pd.concat(siafi_dfs, ignore_index=True)

    reestimativa_columns_to_use = ['ano', 'uo_cod', 'receita_cod', 'fonte_cod', 'vlr_reest_rec']
    reestimativa_df = build_df(
        f'reestimativa_{ANO_REF}', reestimativa_columns_to_use)

    ppo_columns_to_use = ['Ano', 'Código da Unidade', 'Classificação da Receita', 'Fonte', 'Valor LDO']
    ppo_df = build_df(f'ppo_{ANO_REF_LDO}', ppo_columns_to_use)
    ppo_df.rename(columns={'Ano': 'ano',
                           'Código da Unidade': 'uo_cod',
                           'Classificação da Receita': 'receita_cod',
                           'Fonte': 'fonte_cod',
                           'Valor LDO': 'vlr_loa_rec'
                           }, inplace=True)
    ppo_df['receita_cod'] = (ppo_df['receita_cod'].str.replace('.', '', regex=False).astype('Int64'))

    all_columns = list(set(siafi_columns_to_use) |
                       set(reestimativa_columns_to_use) |
                       set(ppo_df.columns))

    for col in all_columns:
        if col not in siafi_columns_to_use:
            siafi_df[col] = np.nan
        if col not in reestimativa_columns_to_use:
            reestimativa_df[col] = np.nan
        if col not in ppo_df.columns:
            ppo_df[col] = np.nan

    valor_painel = pd.concat([siafi_df, reestimativa_df, ppo_df], ignore_index=True).rename(
        columns={'vlr_loa_rec': 'vlr_ldo', 'vlr_reest_rec': 'vlr_reest'})

    # Ajusta o valor painel para o ano de 2025
    valor_painel['valor_painel'] = np.where(
        valor_painel['ano'].isin([ANO_REF_LDO-4, ANO_REF_LDO-3, ANO_REF_LDO-2]),
        valor_painel['vlr_efetivado_ajustado'],
        np.where(
            valor_painel['ano'] == ANO_REF_LDO,
            valor_painel['vlr_ldo'],
            np.where(
                valor_painel['ano'].str.startswith('siafi'),
                valor_painel['vlr_previsto_inicial'],
                np.where(
                    valor_painel['ano'].str.startswith('reestimativa'),
                    valor_painel['vlr_reest'],
                    np.nan))))

    if not valor_painel.empty:
        valor_painel['uo_cod'] = np.where(
            valor_painel['uo_cod'] == 9999, 9901, valor_painel['uo_cod'])
        return valor_painel

    else:
        print("Dataframe valor_painel carregado não possui dados.\n")
        exit(1)


def cria_receita_fonte_analise(valor_painel, df_auxiliar, tipo_base):

    if tipo_base == 'receita':
        group_columns = ['ano', 'uo_cod', 'receita_cod', 'fonte_cod']
        nome_arquivo = 'src/data/receita_analise.csv'
    elif tipo_base == 'fonte':
        group_columns = ['ano', 'uo_cod', 'fonte_cod']
        nome_arquivo = 'src/data/fonte_analise.csv'
    else:
        raise ValueError("A base deve ser do tipo 'receita' ou 'fonte'.")

    # TRATAMENTO DAS BASES
    # BASE CONVENIOS
    base_convenios = valor_painel[valor_painel['fonte_cod'].isin(fontes_convenios)]
    base_convenios = base_convenios.groupby(group_columns)['valor_painel'].sum().reset_index()

    # BASE DEMAIS FONTES
    base_demais = valor_painel[~valor_painel['fonte_cod'].isin(fontes_convenios)]
    base_demais = base_demais.groupby(group_columns)['valor_painel'].sum().reset_index()


    base_convenios = base_convenios.astype({'uo_cod': pd.Int64Dtype(), 'fonte_cod': pd.Int64Dtype()})
    base_demais = base_demais.astype({'uo_cod': pd.Int64Dtype(), 'fonte_cod': pd.Int64Dtype()})

    if 'receita_cod' in base_demais.columns:
        base_demais = base_demais.astype({ 'receita_cod': pd.StringDtype()})
        base_demais['receita_cod'] = base_demais['receita_cod'].fillna('-')

    # BASE ANALISE
    base_analise = pd.concat([base_convenios, base_demais], ignore_index=True)
    filter_columns = group_columns.copy() + ['valor_painel']
    base_analise = base_analise[filter_columns].groupby(group_columns).sum().reset_index()

    # Pivot the table
    pivot_columns = [col for col in group_columns if col != 'ano']
    base_analise = base_analise.pivot_table(index=pivot_columns, columns='ano', values='valor_painel',
                                            aggfunc='sum').reset_index()

    # Fill NaN values with 0 and round to 2 decimal places
    numeric_columns = base_analise.select_dtypes(include=[np.number]).columns.drop(['uo_cod', 'fonte_cod'])
    base_analise[numeric_columns] = base_analise[numeric_columns].fillna(0).round(2)

    # Reorder columns based on specific order
    if 'receita_cod' in base_analise.columns:
        column_order = ['uo_cod', 'receita_cod', 'fonte_cod', ANO_REF - 3, ANO_REF - 2, ANO_REF - 1,
                        f"reestimativa_{ANO_REF}", f"siafi_{ANO_REF}", ANO_REF_LDO]
    else:
        column_order = ['uo_cod', 'fonte_cod', ANO_REF - 3, ANO_REF - 2, ANO_REF - 1,
                        f"reestimativa_{ANO_REF}", f"siafi_{ANO_REF}", ANO_REF_LDO]

    base_analise = base_analise[column_order]


    # ALERTAS
    base_analise.loc[:, 'ano'] = ANO_REF

    # Parametros iniciais
    cols_passado = [ANO_REF - 3, ANO_REF - 2, ANO_REF - 1]
    media_passado = base_analise[cols_passado].sum(axis=1) / 3
    max_passado = base_analise[cols_passado].max(axis=1)
    min_passado = base_analise[cols_passado].min(axis=1)

    if tipo_base == 'receita':
        base_analise['CONVENIOS'] = is_convenios_rec(base_analise)
        base_analise['INTRA_SAUDE'] = is_intra_saude_rec(base_analise)

    # Dicionário de regras
    regras_alertas = [
        # ===== ALERTAS SÓ RECEITA =====
        {"condicao": lambda df: df['INTRA_SAUDE'] == True,
         "alerta": "RECEITA REPASSE FES (LANÇAMENTO SPLOR)",
         "aplica_em": ["receita"]},

        {"condicao": lambda df: df['fonte_cod'].isin(fontes_convenios),
         "alerta": "RECEITA INFORMADA PELA DCGCE/SEPLAG",
         "aplica_em": ["receita"]},

        {"condicao": lambda df: (df['CONVENIOS'] == True) & ~df['fonte_cod'].isin(fontes_convenios),
         "alerta": "RECEITA DE CONVENIOS EM FONTE NAO ESPERADA",
         "aplica_em": ["receita"]},

        # ===== ALERTAS COMUNS =====
        {"condicao": lambda df: ((df[ANO_REF - 3] > 0) & (df[ANO_REF - 2] > 0) &
                                 (df[ANO_REF - 1] > 0) & (df[ANO_REF_LDO] == 0)),
         "alerta": "RECEITA NAO ESTIMADA",
         "aplica_em": ["receita", "fonte"]},

        {"condicao": lambda df: (((df[ANO_REF - 2] > 0) & (df[ANO_REF_LDO] == 0)) |
                                 ((df[ANO_REF - 1] > 0) & (df[ANO_REF_LDO] == 0))),
         "alerta": "ATENCAO",
         "aplica_em": ["receita", "fonte"]},

        {"condicao": lambda df: ((df[ANO_REF_LDO] > 0) & (media_passado > 0) &
                                 (((df[ANO_REF_LDO] > (media_passado * 2)) &
                                   (df[ANO_REF_LDO] > (1.2 * max_passado))) |
                                   ((df[ANO_REF_LDO] < (media_passado / 2)) &
                                    (df[ANO_REF_LDO] < (0.9 * min_passado))))),
         "alerta": "VALOR DISCREPANTE",
         "aplica_em": ["receita", "fonte"]}
    ]

    conditions = []
    choices = []

    for regra in regras_alertas:
        if tipo_base in regra["aplica_em"]:
            conditions.append(regra["condicao"](base_analise))
            choices.append(regra["alerta"])

    base_analise['ALERTAS'] = np.select(conditions, choices, default="OK")


    # Adiciona descrições e remove colunas desnecessárias
    base_analise['ano'] = ANO_REF

    if tipo_base == 'receita':
        base_analise = adiciona_desc(base_analise, ['RECEITA_COD', 'UO_COD', 'FONTE_COD'], overwrite=True)
        base_analise = base_analise.drop(['ANO', 'INTRA_SAUDE', 'CONVENIOS'], axis=1)
        base_analise = base_analise[~((base_analise['UO_COD'] == 4461) | (base_analise['FONTE_COD'] == 58))]
    else:
        base_analise = adiciona_desc(base_analise, ['UO_COD', 'FONTE_COD'], overwrite=True)
        base_analise = base_analise.drop(['ANO'], axis=1)

    base_analise.columns = base_analise.columns.str.lower()
    base_analise.insert(0, 'ano_ref', ANO_REF_LDO)


    base_analise['fonte_cod'] = base_analise['fonte_cod'].astype(str)
    df_aux = df_auxiliar.drop_duplicates(subset=['CD_FONTE'])
    base_analise = base_analise.merge(df_aux, left_on='fonte_cod', right_on='CD_FONTE', how='left')

    base_analise['passivel_analise_dcmefo'] = base_analise['Analise DCMEFO'].apply(
        lambda x: 'Sim' if str(x).strip().upper() == 'SIM' else 'Não')

    base_analise['UO'] = base_analise['uo_cod'].astype(str) + ' - ' + base_analise['uo_sigla']

    base_analise['Fonte de Recursos'] = base_analise['fonte_cod'].astype(str) + ' - ' + base_analise['fonte_desc']

    if 'receita_cod' in base_analise.columns and 'receita_desc' in base_analise.columns:
        base_analise['Classificação da Receita'] = base_analise['receita_cod'].astype(
            str) + ' - ' + base_analise['receita_desc']

    base_analise['Alerta_Visual'] = base_analise['alertas'].apply(lambda x: f"{get_alert_icon(x)} {x}")

    os.makedirs('src/data', exist_ok=True)
    base_analise.to_csv(nome_arquivo, index=False)


def cria_orcamento_analise(df_auxiliar, df_uo, df_fonte_recurso):
    df = pd.read_csv('datapackages/ppo_2027/data/Orcamento_Receita.csv', sep=';', encoding='utf-8',
                     dtype={'Código da Unidade': 'string', 'Fonte': 'string'})

    df['fonte_cod_temp'] = (df['Fonte'].astype(str).str.extract(r'^(\d+)')[0]
                            .fillna(df['Fonte'].astype(str).str.strip()))

    df_aux = df_auxiliar.drop_duplicates(subset=['CD_FONTE'])

    df = df.merge(df_aux, left_on='fonte_cod_temp', right_on='CD_FONTE', how='left')

    df['passivel_analise_dcmefo'] = df['Analise DCMEFO'].apply(
        lambda x: 'Sim' if str(x).strip().upper() == 'SIM' else 'Não')

    df.drop(columns=['fonte_cod_temp'], inplace=True, errors='ignore')

    # Concatenações da base LDO 2027 (Cruzamento com uo.csv já filtrada em 2026)
    df_uo_unique = df_uo[['uo_cod', 'uo_sigla']].drop_duplicates(subset=['uo_cod'])

    df = df.merge(df_uo_unique, left_on='Código da Unidade', right_on='uo_cod', how='left')

    df['uo_sigla'] = df['uo_sigla'].fillna(df['Unidade Orçamentária'].astype(str))

    df['Unidade Orçamentária_concat'] = df['Código da Unidade'].astype(str) + ' - ' + df['Unidade Orçamentária'].astype(str)

    # Concatenações da base LDO 2027 (Cruzamento com fonte_recurso.csv já filtrada em 2026)
    df_fr_unique = df_fonte_recurso[['fonte_cod', 'fonte_desc']].drop_duplicates(subset=['fonte_cod'])

    df = df.merge(df_fr_unique, left_on='Fonte', right_on='fonte_cod', how='left')

    df['fonte_desc'] = df['fonte_desc'].fillna('')

    df.loc[df['fonte_desc'].astype(str).str.strip() != '', 'Fonte_concat'] = (df['Fonte'].astype(str) + ' - ' + df['fonte_desc'])

    df.drop(columns=['fonte_cod', 'Fonte_str'], inplace=True, errors='ignore')

    df['Classificação da Receita_concat'] = df['Classificação da Receita'].astype(str) + ' - ' + df['Descrição da Receita'].astype(str)

    df['Valor LDO'] = (df['Valor LDO'].astype(str)
                       .str.replace('.', '', regex=False)
                       .str.replace(',', '.', regex=False)
                       .pipe(pd.to_numeric, errors='coerce')
                       .fillna(0))

    df.to_csv('src/data/orcamento_analise.csv', index=False)

    return


def cria_dcmefo_analise():
    df = pd.read_csv('datapackages/tabelas_auxiliares/analise_dcmefo.csv', sep=';', encoding='utf-8')

    df['Unidade Orçamentária_concat'] = df['uo_cod'].astype(str) + ' - ' + df['uo_sigla'].astype(str)

    df['Fonte de recursos_concat'] = df['fonte_cod'].astype(str) + ' - ' + df['fonte_desc'].astype(str)

    df.to_csv('src/data/dcmefo_analise.csv', index=False)

    return
