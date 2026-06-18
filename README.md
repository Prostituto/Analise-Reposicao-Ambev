# Sistema de Análise de Reposição — Revalle Sisal

Sistema web interno desenvolvido em Python/Flask para gestão, análise e acompanhamento de reposições de produtos nos pontos de venda (PDVs) da Revalle Sisal.

---

## Funcionalidades

### Dashboard de Gestão
- Resumo do período com contagem e percentual por categoria de status
- Tempo médio entre lançamento e aprovação (apenas reposições aprovadas)
- Download de relatórios PDF de Canceladas/Devolvidas e Limbo

### Análises Visuais (Gráficos Interativos)
| Gráfico | Descrição |
|---|---|
| Evolução Mensal | Barras sobrepostas com total × entregues por mês + linha de eficiência (%) |
| Distribuição por Status | Donut com legenda detalhada: Entregue, Reprovada, Devolvida, Cancelada, Limbo, Pendente |
| Lançamentos por Dia da Semana | Concentração operacional por dia útil vs fim de semana |
| Top 8 Motoristas | Motoristas com mais reposições — clicável para ver detalhes por produto e motivo |
| Top 8 Produtos | Produtos mais repostos no período |
| Top 10 PDVs | Pontos de venda com maior demanda de reposição |
| Tempo de Aprovação | Histograma de dias entre lançamento e aprovação (com linhas de média e mediana) |
| Motivos de Reposição | Top 10 justificativas mais frequentes |

### Comparativo de Períodos
- Comparação de reposições entregues por dia entre dois meses/anos distintos

### Consulta por PDV
- Busca rápida por código do PDV com histórico de todas as reposições
- Exibe status, NF, produto, quantidade, datas de lançamento e aprovação

### Importação de Dados
- Cole o conteúdo do CSV diretamente na interface (sem limite de tamanho)
- Detecção automática de encoding (UTF-8, Latin-1, CP1252) e separador (`;`, `,`, `\t`)
- O arquivo é salvo como `dados.csv` e passa a ser a base de todos os relatórios

### Relatórios PDF
- **Canceladas/Devolvidas**: listagem de reposições com NF_Status C ou D no período
- **Limbo**: reposições aprovadas sem NF válida (não são Entregues, Canceladas nem Devolvidas) — em formato A4 paisagem com colunas: PDV, Produto, Quantidade, Unidade, Solicitação, Data Lançamento, Data Aprovação, Dias desde Aprovação, Status NF

---

## Categorias de Status

| Categoria | Critério |
|---|---|
| **Entregue** | `Status = aprovada` e `NF_Status = E` |
| **Limbo** | `Status = aprovada` e `NF_Status` não é E, C nem D |
| **Pendente** | `Status = pendente` |
| **Cancelada** | `NF_Status = C` |
| **Devolvida** | `NF_Status = D` |
| **Reprovada** | `Status = reprovada` |

---

## Estrutura do Projeto

```
├── app.py            # Aplicação Flask — rotas, templates HTML, lógica de interface
├── processador.py    # Processamento de dados, geração de resumo e chamada dos gráficos
├── graficos.py       # Todos os gráficos Plotly (9 tipos)
├── dados.csv         # Base de dados importada pelo usuário (gerada via interface)
└── README.md
```

---

## Requisitos

```
flask
pandas
plotly
reportlab
```

Instale com:
```bash
pip install flask pandas plotly reportlab
```

---

## Como executar

```bash
python app.py
```

Acesse em: `http://127.0.0.1:5000`

**Primeiro uso:** acesse a aba **Importar Dados** e cole o conteúdo do CSV exportado do sistema de reposições antes de gerar qualquer relatório.

---

## Formato esperado do CSV

O sistema lê as colunas pelas posições (índice):

| Índice | Conteúdo |
|---|---|
| 2 | Código do PDV |
| 4 | Número da Solicitação |
| 6 | Data de Lançamento (`dd/mm/yyyy`) |
| 8 | Status (`aprovada`, `pendente`, `reprovada`) |
| 9 | Data de Aprovação (`dd/mm/yyyy`) |
| 13 | Status NF (`E`, `C`, `D`) |
| 14 | Código do Produto |
| 15 | Descrição do Produto |
| 16 | Quantidade |
| 17 | Unidade |
| 22 | Justificativa / Motivo |
| 34 | Nome do Motorista |
