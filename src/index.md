---
toc: false
theme: [air, ocean-floor, wide]
---

<link rel='stylesheet' href='./styles.css'>

# Painel LDO

```js
// Imports ---------------------------------------------------------------------
import * as Inputs from 'npm:@observablehq/inputs';


// Leitura das bases -----------------------------------------------------------
const receita = await FileAttachment('data/receita_analise.csv').csv();
const fonte = await FileAttachment('data/fonte_analise.csv').csv();
const orcamento = await FileAttachment('data/orcamento_analise.csv').csv();
const dcmefo = await FileAttachment('data/dcmefo_analise.csv').csv();


// Bases filtradas -------------------------------------------------------------
const Searchreceita = Inputs.search(receita);
const SearchValuereceita = view(Searchreceita);

const Searchfonte = Inputs.search(fonte);
const SearchValuefonte = view(Searchfonte);

const Searchorcamento = Inputs.search(orcamento);
const SearchValueorcamento = view(Searchorcamento);

const Searchdcmefo = Inputs.search(dcmefo);
const SearchValuedcmefo = view(Searchdcmefo);


// Contagem dos resumos --------------------------------------------------------
const CountAlertasreceita = receita.reduce((acc, d) => {
  const alerta = d['alertas'];
  acc[alerta] = (acc[alerta] || 0) + 1;
  return acc;
}, {});

const CountAlertasfonte = fonte.reduce((acc, d) => {
  const alerta = d['alertas'];
  acc[alerta] = (acc[alerta] || 0) + 1;
  return acc;
}, {});

const totalLDO = orcamento.reduce((acc, d) => {
  const valor = Number(
    String(d['Valor LDO'])
      .replaceAll('.', '')   // remove milhar
      .replace(',', '.')     // troca decimal
  );
  return acc + (isNaN(valor) ? 0 : valor);
}, 0);

const totalLDOFormatado = totalLDO.toLocaleString('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
});
```

---

## Visão Geral - Previsão de Receitas

### 📊 Resumo de Alertas

<div class='resumo'>
  <div>🟢 OK<br><b>${CountAlertasreceita['OK'] || 0}</b></div>
  <div>📌 INFORMADA<br><b>${CountAlertasreceita['RECEITA INFORMADA PELA DCGCE/SEPLAG'] || 0}</b></div>
  <div>🔴 NÃO ESTIMADA<br><b>${CountAlertasreceita['RECEITA NAO ESTIMADA'] || 0}</b></div>
  <div>🟠 ATENÇÃO<br><b>${CountAlertasreceita['ATENCAO'] || 0}</b></div>
  <div>⚠️ DISCREPANTE<br><b>${CountAlertasreceita['VALOR DISCREPANTE'] || 0}</b></div>
  <div>📌 REPASSE FES<br><b>${CountAlertasreceita['RECEITA REPASSE FES (LANÇAMENTO SPLOR)'] || 0}</b></div>
  <div>🟤 CONVENIOS EM FONTE NÃO ESPERADA<br><b>${CountAlertasreceita['RECEITA DE CONVENIOS EM FONTE NAO ESPERADA'] || 0}</b></div>
</div>


<div class='card' style='padding: 0'>
  <div style='padding: 1em'>
    ${display(Searchreceita)}
  </div>
  ${display(Inputs.table(SearchValuereceita, {
    columns: [
      'uo_cod',
      'uo_sigla',
      'receita_cod',
      'receita_desc',
      'fonte_cod',
      'fonte_desc',
      '2024',
      '2025',
      'reestimativa_2026',
      '2027',
      'Alerta_Visual',
    ],
    header: {
      uo_cod: 'UO cod',
      uo_sigla: 'UO',
      receita_cod: 'Classificação Receita cod',
      receita_desc: 'Classificação da Receita',
      fonte_cod: 'Fonte cod',
      fonte_desc: 'Fonte de Recursos',
      2024: '2024',
      2025: '2025',
      reestimativa_2026: '2026 Reest',
      2027: '2027 LDO',
      Alerta_Visual: 'Alertas',
    },
    width: {
      uo_cod: 75,
      uo_sigla: 75,
      receita_cod: 150,
      receita_desc: 500,
      fonte_cod: 75,
      fonte_desc: 500,
      2024: 100,
      2025: 100,
      reestimativa_2026: 100,
      2027: 100,
      Alerta_Visual: 200,
    },
    align: {
      2024: 'right',
      2025: 'right',
      reestimativa_2026: 'right',
      2027: 'right',
    },
  }))}
</div>

---

## Análise por Fonte de Recursos

### 📊 Resumo de Alertas

<div class='resumo'>
  <div>🟢 OK<br><b>${CountAlertasfonte['OK'] || 0}</b></div>
  <div>📌 INFORMADA<br><b>${CountAlertasfonte['RECEITA INFORMADA PELA DCGCE/SEPLAG'] || 0}</b></div>
  <div>🔴 NÃO ESTIMADA<br><b>${CountAlertasfonte['RECEITA NAO ESTIMADA'] || 0}</b></div>
  <div>🟠 ATENÇÃO<br><b>${CountAlertasfonte['ATENCAO'] || 0}</b></div>
  <div>⚠️ DISCREPANTE<br><b>${CountAlertasfonte['VALOR DISCREPANTE'] || 0}</b></div>
  <div>📌 REPASSE FES<br><b>${CountAlertasfonte['RECEITA REPASSE FES (LANÇAMENTO SPLOR)'] || 0}</b></div>
  <div>🟤 CONVENIOS EM FONTE NÃO ESPERADA<br><b>${CountAlertasfonte['RECEITA DE CONVENIOS EM FONTE NAO ESPERADA'] || 0}</b></div>
</div>

<div class='card' style='padding: 0'>
  <div style='padding: 1em'>
    ${display(Searchfonte)}
  </div>
  ${display(Inputs.table(SearchValuefonte, {
    columns: [
      'uo_cod',
      'uo_sigla',
      'fonte_cod',
      'fonte_desc',
      '2024',
      '2025',
      'reestimativa_2026',
      '2027',
      'Alerta_Visual',
    ],
    header: {
      uo_cod: 'UO cod',
      uo_sigla: 'UO',
      fonte_cod: 'Fonte cod',
      fonte_desc: 'Fonte de Recursos',
      2024: '2024',
      2025: '2025',
      reestimativa_2026: '2026 Reest',
      2027: '2027 LDO',
      Alerta_Visual: 'Alertas',
    },
    format: {
      '2024': (x) => x.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      '2025': (x) => x.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      'reestimativa_2026': (x) => x.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
      '2027': (x) => x.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }),
    },
    width: {
      uo_cod: 75,
      uo_sigla: 75,
      fonte_cod: 75,
      fonte_desc: 500,
      2024: 100,
      2025: 100,
      reestimativa_2026: 100,
      2027: 100,
      Alerta_Visual: 200,
    },
    align: {
      2024: 'right',
      2025: 'right',
      reestimativa_2026: 'right',
      2027: 'right',
    },
  }))}
</div>

---

## LDO 2027

### 💰 Valor Total LDO

<div class='card', style='margin-top: 8px;'>
  <div style='font-size: 20px; padding: 8px;'>
  R$ ${totalLDO.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
  </div>
</div>

<div class='card' style='padding: 0'>
  <div style='padding: 1em'>
    ${display(Searchorcamento)}
  </div>
  ${display(Inputs.table(SearchValueorcamento, {
    columns: [
      'Unidade Orçamentária_concat',
      'Fonte_concat',
      'Classificação da Receita_concat',
      'Metodologia de cálculo e premissas utilizadas',
      'Valor LDO',
    ],
    header: {
      'Unidade Orçamentária_concat': 'Unidade Orçamentária',
      'Fonte_concat': 'Fonte de Recursos',
      'Classificação da Receita_concat': 'Classificação da Receita',
      'Metodologia de cálculo e premissas utilizadas': 'Metodologia e Premissas',
      'Valor LDO': 'Valor LDO',
    },
    width: {
      'Unidade Orçamentária_concat': 150,
      'Fonte_concat': 300,
      'Classificação da Receita_concat': 400,
      'Metodologia de cálculo e premissas utilizadas': 500,
      'Valor LDO': 100,
    },
    align: {
      'Valor LDO': 'right',
    },
  }))}
</div>

---

## Análise DCMEFO

### 📋 Detalhamento (Análise DCMEFO)

<div class='card' style='padding: 0'>
  <div style='padding: 1em'>
    ${display(Searchdcmefo)}
  </div>
  ${display(Inputs.table(SearchValuedcmefo, {
    columns: [
      'Unidade Orçamentária_concat',
      'Fonte de recursos_concat',
      'analise_dcmefo',
    ],
    header: {
      'Unidade Orçamentária_concat': 'Unidade Orçamentária',
      'Fonte de recursos_concat': 'Fonte de recursos',
      'analise_dcmefo': 'Análise DCMEFO',
    },
    width: {
      'Unidade Orçamentária_concat': 150,
      'Fonte de recursos_concat': 300,
      'analise_dcmefo': 150,
    },
  }))}
</div>
