import pandas as pd
from graficos import (gerar_grafico, grafico_top_motoristas, grafico_top_produtos,
                      gerar_grafico_motivo_reposicao, grafico_donut_status,
                      grafico_top_pdvs, grafico_tempo_aprovacao, grafico_dia_semana)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path
import sys

# === Paths base ===
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DADOS_CSV = BASE_DIR / "dados.csv"


def _carregar_dados():
    """Lê dados.csv importado pelo usuário. Levanta erro se não existir."""
    if not DADOS_CSV.exists():
        raise FileNotFoundError("Nenhum arquivo importado. Acesse 'Importar Dados' para carregar o CSV.")
    for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
        try:
            with open(DADOS_CSV, 'r', encoding=enc) as f:
                primeira_linha = f.readline()
            sep = ';' if ';' in primeira_linha else ('\t' if '\t' in primeira_linha else ',')
            return pd.read_csv(DADOS_CSV, sep=sep, header=0,
                               dtype=str, keep_default_na=False, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Não foi possível ler dados.csv (encoding inválido).")


# ===========================
# PDF: Canceladas e Devolvidas
# ===========================
def gerar_pdf_canceladas_devolvidas(data_inicio, data_fim, caminho_pdf="relatorio_canceladas_devolvidas.pdf"):
    df = _carregar_dados()

    # Normalização
    df.columns = df.columns.str.strip()
    df['Data_Lancamento'] = pd.to_datetime(df.iloc[:, 6], errors='coerce', dayfirst=True)  # G
    df['NF_Status'] = df.iloc[:, 13].astype(str).str.strip().str.upper()    # N

    # Período por Data de Lançamento
    df = df[(df['Data_Lancamento'] >= data_inicio) & (df['Data_Lancamento'] <= data_fim)]

    # Somente Canceladas (C) e Devolvidas (D)
    df_filtrado = df[df['NF_Status'].isin(['C', 'D'])]

    # Seleção de colunas para relatório:
    # C (idx 2) = PDV | O (idx 14) = Código Produto | Q (idx 16) = Quantidade | R (idx 17) = Unidade
    df_relatorio = df_filtrado.iloc[:, [2, 14, 16, 17]].copy()
    df_relatorio.columns = ['PDV', 'Código Produto', 'Quantidade', 'Unidade']

    # Construção do PDF
    doc = SimpleDocTemplate(caminho_pdf, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()

    elementos.append(Paragraph("Relatório - Reposições Canceladas e Devolvidas", styles['Title']))
    elementos.append(Spacer(1, 12))

    dados_tabela = [list(df_relatorio.columns)] + df_relatorio.values.tolist()
    tabela = Table(dados_tabela, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))

    elementos.append(tabela)
    doc.build(elementos)
    return caminho_pdf


# ==============
# PDF: Limbo
# ==============
def gerar_pdf_limbo(data_inicio, data_fim, caminho_pdf="relatorio_limbo.pdf"):
    """
    Limbo = Reposições APROVADAS (coluna I) com NF_Status (coluna N) diferente de E, C ou D.
    Período do relatório: Data de Lançamento (G) entre [data_inicio, data_fim].
    Mesmo critério usado na linha 'Limbo' do resumo do dashboard.
    """
    df = _carregar_dados()

    df.columns = df.columns.str.strip()
    df['Data_Lancamento'] = pd.to_datetime(df.iloc[:, 6], errors='coerce', dayfirst=True)   # G
    df['Status'] = df.iloc[:, 8].astype(str).str.strip().str.lower()         # I
    df['Data_Aprov'] = pd.to_datetime(df.iloc[:, 9], errors='coerce', dayfirst=True)        # J
    df['NF_Status'] = df.iloc[:, 13].astype(str).str.strip().str.upper()     # N

    # Período por Data de Lançamento (igual ao resumo)
    df_periodo = df[(df['Data_Lancamento'] >= data_inicio) &
                    (df['Data_Lancamento'] <= data_fim)].copy()

    # Limbo: aprovada sem NF válida, com mais de 1 dia desde a aprovação
    hoje = pd.Timestamp.today().normalize()
    _base_limbo = df_periodo[
        (df_periodo['Status'] == 'aprovada') &
        (~df_periodo['NF_Status'].isin(['E', 'C', 'D']))
    ].copy()
    _base_limbo['Dias_desde_aprov'] = _base_limbo['Data_Aprov'].apply(
        lambda d: int((hoje - d).days) if pd.notna(d) else None
    )
    # Exclui registros com 0 ou 1 dia desde aprovação (aprovação muito recente)
    df_limbo = _base_limbo[
        _base_limbo['Dias_desde_aprov'].isna() | (_base_limbo['Dias_desde_aprov'] > 1)
    ].copy()

    base_indices = [2, 14, 16, 17, 4]  # PDV, Código, Quantidade, Unidade, Solicitação

    doc = SimpleDocTemplate(caminho_pdf, pagesize=landscape(A4),
                            leftMargin=30, rightMargin=30, topMargin=36, bottomMargin=36)
    elementos = []
    styles = getSampleStyleSheet()
    elementos.append(Paragraph("Relatório - Reposições em Limbo", styles['Title']))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(
        f"Período (por Data de Lançamento): {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}",
        styles['BodyText']
    ))
    elementos.append(Spacer(1, 8))

    if df_limbo.empty or any(i >= len(df_limbo.columns) for i in base_indices):
        elementos.append(Paragraph("Não há reposições no limbo no período selecionado.", styles['BodyText']))
        doc.build(elementos)
        return caminho_pdf

    df_relatorio = df_limbo.iloc[:, base_indices].copy()
    df_relatorio.columns = ['PDV', 'Código Produto', 'Quantidade', 'Unidade', 'Solicitação']
    df_relatorio['Data Lançamento'] = df_limbo['Data_Lancamento'].dt.strftime('%d/%m/%Y')
    df_relatorio['Data Aprovação'] = df_limbo['Data_Aprov'].apply(
        lambda d: d.strftime('%d/%m/%Y') if pd.notna(d) else '-'
    )
    df_relatorio['Dias desde aprovação'] = df_limbo['Dias_desde_aprov'].apply(
        lambda v: int(v) if v is not None else '-'
    )
    df_relatorio['Status NF'] = df_limbo['NF_Status']

    # Larguras fixas somando 781pt (A4 paisagem 841pt − margens 30+30pt)
    col_widths = [55, 105, 70, 55, 75, 90, 90, 126, 115]

    dados_tabela = [list(df_relatorio.columns)] + df_relatorio.values.tolist()
    tabela = Table(dados_tabela, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.orange),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('WORDWRAP', (0,0), (-1,0), True),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
    ]))

    elementos.append(tabela)
    doc.build(elementos)
    return caminho_pdf


# ==================
# Dashboard: Resumo
# ==================
def gerar_relatorio(data_inicio, data_fim):
    df = _carregar_dados()

    # Normalização de colunas e campos usados
    df.columns = df.columns.str.strip()
    df['Data_Lancamento'] = pd.to_datetime(df.iloc[:, 6], errors='coerce', dayfirst=True)  # G
    df['Status'] = df.iloc[:, 8].astype(str).str.strip().str.lower()        # I
    df['Data_Aprov'] = pd.to_datetime(df.iloc[:, 9], errors='coerce', dayfirst=True)       # J
    df['NF_Status'] = df.iloc[:, 13].astype(str).str.strip().str.upper()    # N

    # Filtra por Data de Lançamento para os indicadores do período selecionado
    df = df[(df['Data_Lancamento'] >= data_inicio) & (df['Data_Lancamento'] <= data_fim)]

    # ===== Tempo médio entre lançamento e aprovação (apenas aprovadas do período lançado) =====
    df_aprovadas = df[(df['Status'] == 'aprovada') & df['Data_Aprov'].notna() & df['Data_Lancamento'].notna()].copy()
    if not df_aprovadas.empty:
        df_aprovadas['Dias_entre'] = (df_aprovadas['Data_Aprov'] - df_aprovadas['Data_Lancamento']).dt.days
        # descarta valores negativos (eventuais erros de digitação)
        df_aprovadas = df_aprovadas[df_aprovadas['Dias_entre'] >= 0]
        media_dias_entrega = float(df_aprovadas['Dias_entre'].mean()) if not df_aprovadas.empty else None
    else:
        media_dias_entrega = None

    # Gráfico Motivo de Reposição (usa coluna 'Justificativa' presente na planilha)
    grafico_motivo_reposicao = gerar_grafico_motivo_reposicao(df)

    # Resumo (contagens e % sobre o período selecionado por Data_Lancamento)
    resumo = {}
    total = df.shape[0] if df.shape[0] > 0 else 1

    entregue = df[(df['Status'] == 'aprovada') & (df['NF_Status'] == 'E')]
    resumo['Reposição Entregue'] = [entregue.shape[0], f"{(entregue.shape[0] / total) * 100:.2f}%"]

    _hoje = pd.Timestamp.today().normalize()
    _dias_aprov = ((_hoje - df['Data_Aprov']).dt.days)
    _limbo_mask = (
        (df['Status'] == 'aprovada') &
        (~df['NF_Status'].isin(['E', 'C', 'D'])) &
        (_dias_aprov.isna() | (_dias_aprov > 1))
    )
    aprovada_sem_nf = df[_limbo_mask]
    resumo['Limbo'] = [aprovada_sem_nf.shape[0], f"{(aprovada_sem_nf.shape[0] / total) * 100:.2f}%"]

    pendente = df[df['Status'] == 'pendente']
    resumo['Pendente de Aprovação'] = [pendente.shape[0], f"{(pendente.shape[0] / total) * 100:.2f}%"]

    perdida_cancelada = df[df['NF_Status'] == 'C']
    resumo['Reposição Perdida - Cancelada'] = [perdida_cancelada.shape[0], f"{(perdida_cancelada.shape[0] / total) * 100:.2f}%"]

    perdida_devolvida = df[df['NF_Status'] == 'D']
    resumo['Reposição Perdida - Devolvida'] = [perdida_devolvida.shape[0], f"{(perdida_devolvida.shape[0] / total) * 100:.2f}%"]

    reprovada = df[df['Status'] == 'reprovada']
    resumo['Reposição Perdida - Reprovada'] = [reprovada.shape[0], f"{(reprovada.shape[0] / total) * 100:.2f}%"]

    # Adiciona o total no final
    total_reposicoes = df.shape[0]
    resumo['TOTAL DE REPOSIÇÕES LANÇADAS'] = [total_reposicoes, '100.00%']

    # Gráficos
    graficos = {
        'evolucao':    gerar_grafico(df),
        'motoristas':  grafico_top_motoristas(df),
        'produtos':    grafico_top_produtos(df),
        'motivo':      grafico_motivo_reposicao,
        'donut':       grafico_donut_status(df),
        'top_pdvs':    grafico_top_pdvs(df),
        'tempo':       grafico_tempo_aprovacao(df),
        'dia_semana':  grafico_dia_semana(df),
    }

    return resumo, graficos, media_dias_entrega
