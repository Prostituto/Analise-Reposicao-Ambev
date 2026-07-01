import plotly.graph_objects as go
import pandas as pd
import locale
from datetime import datetime

try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except Exception:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')
    except Exception:
        pass

# ── Paleta e layout base ───────────────────────────────────────────────────────
_BLUE   = '#2563eb'
_GREEN  = '#16a34a'
_RED    = '#dc2626'
_YELLOW = '#ca8a04'
_PURPLE = '#7c3aed'
_TEAL   = '#0891b2'
_ORANGE = '#ea580c'

_BASE = dict(
    font=dict(family="Inter,system-ui,sans-serif", size=11.5, color="#1e293b"),
    paper_bgcolor="white",
    plot_bgcolor="#f8fafc",
    margin=dict(l=48, r=24, t=52, b=44),
    height=320,
    autosize=True,
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#1e293b", font_size=12,
                    font_color="white"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font_size=11),
    xaxis=dict(gridcolor="#e2e8f0", linecolor="#e2e8f0", tickfont_size=11, zeroline=False),
    yaxis=dict(gridcolor="#e2e8f0", linecolor="#e2e8f0", tickfont_size=11, zeroline=False),
    title=dict(font=dict(size=13, color="#1e293b"), x=0, xref='paper', pad=dict(l=0, t=4)),
)

def _render(fig, div_id=None):
    fig.update_layout(**_BASE)
    kw = dict(full_html=False, include_plotlyjs='cdn',
              config={'responsive': True, 'displayModeBar': False})
    if div_id:
        kw['div_id'] = div_id
    return fig.to_html(**kw)

_DIAS_PT = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']


# ── 1. Evolução mensal: barras total + entregues + linha % ─────────────────────
def gerar_grafico(df):
    d = df.copy()
    d['_ano'] = d['Data_Lancamento'].dt.year
    d['_mes'] = d['Data_Lancamento'].dt.month
    d['_rot'] = d['Data_Lancamento'].dt.strftime('%b/%y')

    total    = d.groupby(['_ano','_mes','_rot']).size().reset_index(name='Total')
    entregue = (d[(d['Status']=='aprovada') & (d['NF_Status']=='E')]
                .groupby(['_ano','_mes','_rot']).size().reset_index(name='Entregues'))

    m = total.merge(entregue, on=['_ano','_mes','_rot'], how='left').fillna(0)
    m['Pct'] = (m['Entregues'] / m['Total'].replace(0,1) * 100).round(1)
    m = m.sort_values(['_ano','_mes'])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=m['_rot'], y=m['Total'], name='Total lançadas',
        marker_color='#dbeafe', hovertemplate='%{y} lançadas<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        x=m['_rot'], y=m['Entregues'], name='Entregues',
        marker_color=_BLUE, hovertemplate='%{y} entregues<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=m['_rot'], y=m['Pct'], mode='lines+markers+text',
        text=[f"{v:.0f}%" for v in m['Pct']], textposition='top center',
        textfont=dict(size=10, color=_RED),
        name='% Entregue', yaxis='y2',
        line=dict(color=_RED, width=2), marker=dict(size=5, color=_RED),
        hovertemplate='%{y:.1f}%<extra></extra>',
    ))
    fig.update_layout(
        title='Evolução Mensal de Reposições',
        barmode='overlay',
        yaxis=dict(title='Quantidade'),
        yaxis2=dict(title='% Entregues', overlaying='y', side='right',
                    range=[0, 115], showgrid=False, ticksuffix='%', tickfont_size=11),
        legend=dict(orientation='h', y=-0.22, x=0.5, xanchor='center'),
        height=380,
    )
    return _render(fig)


# ── 2. Comparativo entre dois meses ──────────────────────────────────────────
def gerar_grafico_comparativo(df, mes1, ano1, mes2, ano2):
    def _por_dia(dfx):
        e = dfx[(dfx['Status']=='aprovada') & (dfx['NF_Status']=='E')]
        return e.groupby(dfx['Data_Lancamento'].dt.day).size().reset_index(name='Qtd')

    d1 = _por_dia(df[(df['Data_Lancamento'].dt.month==mes1)&(df['Data_Lancamento'].dt.year==ano1)])
    d2 = _por_dia(df[(df['Data_Lancamento'].dt.month==mes2)&(df['Data_Lancamento'].dt.year==ano2)])
    nm1 = datetime(ano1, mes1, 1).strftime('%b/%y')
    nm2 = datetime(ano2, mes2, 1).strftime('%b/%y')

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d1['Data_Lancamento'], y=d1['Qtd'], name=nm1,
        mode='lines+markers', line=dict(color=_BLUE, width=2), marker_size=5,
        fill='tozeroy', fillcolor='rgba(37,99,235,.09)',
        hovertemplate='Dia %{x}: %{y}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=d2['Data_Lancamento'], y=d2['Qtd'], name=nm2,
        mode='lines+markers', line=dict(color=_RED, width=2), marker_size=5,
        fill='tozeroy', fillcolor='rgba(220,38,38,.09)',
        hovertemplate='Dia %{x}: %{y}<extra></extra>',
    ))
    fig.update_layout(
        title='Comparativo de Reposições Entregues por Dia',
        xaxis=dict(title='Dia do mês', dtick=1),
        yaxis_title='Quantidade', height=360,
    )
    return _render(fig)


# ── 3. Donut de distribuição de status ───────────────────────────────────────
def grafico_donut_status(df):
    entregue  = int(((df['Status']=='aprovada') & (df['NF_Status']=='E')).sum())
    pendente  = int((df['Status']=='pendente').sum())
    reprovada = int((df['Status']=='reprovada').sum())
    devolvida = int((df['NF_Status']=='D').sum())
    cancelada = int((df['NF_Status']=='C').sum())
    _hoje = pd.Timestamp.today().normalize()
    _dias = ((_hoje - df['Data_Aprov']).dt.days)
    limbo = int(((df['Status']=='aprovada') & (~df['NF_Status'].isin(['E','C','D'])) &
                 (_dias.isna() | (_dias > 1))).sum())

    items = [
        ('Entregue',  entregue,  _BLUE),
        ('Reprovada', reprovada, _RED),
        ('Devolvida', devolvida, _ORANGE),
        ('Cancelada', cancelada, '#475569'),
        ('Limbo',     limbo,     _PURPLE),
        ('Pendente',  pendente,  _YELLOW),
    ]
    total = sum(v for _, v, _ in items) or 1

    # Legenda inclui contagem e % — sem nenhum texto nas fatias
    legend_labels = [f"  {n}  —  {v}  ({v/total*100:.1f}%)" for n, v, _ in items]
    vals  = [v for _, v, _ in items]
    cores = [c for _, _, c in items]

    fig = go.Figure(go.Pie(
        labels=legend_labels,
        values=vals,
        hole=.62,
        marker=dict(colors=cores, line=dict(color='white', width=3)),
        textinfo='none',
        hovertemplate='<b>%{label}</b><br>%{value} reposições<extra></extra>',
        direction='clockwise',
        sort=False,
    ))
    fig.add_annotation(
        text=f"<b>{total}</b><br><span style='color:#64748b;font-size:11px'>reposições</span>",
        showarrow=False, font=dict(size=20, color='#1e293b'), align='center',
    )
    fig.update_layout(
        title='Distribuição por Status',
        showlegend=True,
        legend=dict(
            orientation='v', x=1.04, y=0.5,
            xanchor='left', yanchor='middle',
            font=dict(size=12), itemsizing='constant', bgcolor='rgba(0,0,0,0)',
        ),
        height=340,
        margin=dict(l=10, r=10, t=52, b=10),
    )
    return _render(fig)


# ── 4. Top 10 PDVs com mais reposições ───────────────────────────────────────
def grafico_top_pdvs(df):
    serie = df.iloc[:, 2].astype(str).str.strip()
    top = serie.value_counts().nlargest(10).reset_index()
    top.columns = ['PDV', 'Qtd']
    top = top.sort_values('Qtd')

    fig = go.Figure(go.Bar(
        x=top['Qtd'], y=top['PDV'], orientation='h',
        marker=dict(color=top['Qtd'],
                    colorscale=[[0,'#bfdbfe'],[0.5,'#60a5fa'],[1,'#1d4ed8']],
                    showscale=False),
        text=top['Qtd'], textposition='outside',
        hovertemplate='PDV %{y}: %{x} reposições<extra></extra>',
    ))
    fig.update_layout(
        title='Top 10 PDVs com Mais Reposições',
        xaxis_title='Quantidade',
        height=360, margin=dict(l=90, r=40, t=52, b=44),
    )
    return _render(fig)


# ── 5. Lançamentos por dia da semana ─────────────────────────────────────────
def grafico_dia_semana(df):
    d = df.copy()
    d['DiaSem'] = d['Data_Lancamento'].dt.dayofweek
    por_dia = d.groupby('DiaSem').size().reindex(range(7), fill_value=0)

    cores = [_BLUE if i < 5 else '#94a3b8' for i in range(7)]
    fig = go.Figure(go.Bar(
        x=_DIAS_PT, y=por_dia.values,
        marker_color=cores,
        text=por_dia.values, textposition='outside',
        hovertemplate='%{x}: %{y} lançamentos<extra></extra>',
    ))
    fig.update_layout(
        title='Lançamentos por Dia da Semana',
        yaxis_title='Quantidade',
        height=300, margin=dict(l=48, r=24, t=52, b=44),
    )
    return _render(fig)


# ── 6. Histograma de tempo de aprovação ──────────────────────────────────────
def grafico_tempo_aprovacao(df):
    ap = df[(df['Status']=='aprovada') & df['Data_Aprov'].notna() & df['Data_Lancamento'].notna()].copy()
    if ap.empty:
        return None
    ap['Dias'] = (ap['Data_Aprov'] - ap['Data_Lancamento']).dt.days
    ap = ap[ap['Dias'] >= 0]
    if ap.empty:
        return None

    media   = ap['Dias'].mean()
    mediana = ap['Dias'].median()

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ap['Dias'], nbinsx=25,
        marker_color=_BLUE, opacity=.82,
        hovertemplate='%{x} dias: %{y} aprovações<extra></extra>',
        name='Distribuição',
    ))
    fig.add_vline(x=media, line_dash='dash', line_color=_RED, line_width=1.5,
                  annotation_text=f"  Média {media:.1f}d",
                  annotation_position="top right", annotation_font_size=11)
    fig.add_vline(x=mediana, line_dash='dot', line_color=_GREEN, line_width=1.5,
                  annotation_text=f"  Mediana {mediana:.1f}d",
                  annotation_position="top left", annotation_font_size=11)
    fig.update_layout(
        title='Distribuição do Tempo de Aprovação (dias)',
        xaxis_title='Dias entre lançamento e aprovação',
        yaxis_title='Nº de reposições',
        height=300,
    )
    return _render(fig)


# ── 7. Top motoristas (horizontal, clicável) ─────────────────────────────────
def grafico_top_motoristas(df):
    serie = df.iloc[:, 34].dropna().astype(str).str.strip()
    serie = serie[serie.str.len() > 0]
    if serie.empty:
        return None
    top = serie.value_counts().nlargest(8).reset_index()
    top.columns = ['Motorista', 'Qtd']
    top = top.sort_values('Qtd')

    fig = go.Figure(go.Bar(
        x=top['Qtd'], y=top['Motorista'], orientation='h',
        marker_color=_BLUE,
        text=top['Qtd'], textposition='outside',
        hovertemplate='%{y}: %{x} reposições<extra></extra>',
    ))
    fig.update_layout(
        title='Top 8 Motoristas com Mais Reposições',
        xaxis_title='Quantidade',
        height=340, margin=dict(l=150, r=40, t=52, b=44),
    )
    return _render(fig, div_id='grafico_motoristas')


# ── 8. Top produtos ───────────────────────────────────────────────────────────
def grafico_top_produtos(df):
    serie = df.iloc[:, 15].dropna().astype(str).str.strip()
    top = serie.value_counts().nlargest(8).reset_index()
    top.columns = ['Produto', 'Qtd']
    top = top.sort_values('Qtd')

    fig = go.Figure(go.Bar(
        x=top['Qtd'], y=top['Produto'], orientation='h',
        marker_color=_GREEN,
        text=top['Qtd'], textposition='outside',
        hovertemplate='%{y}: %{x}<extra></extra>',
    ))
    fig.update_layout(
        title='Top 8 Produtos Mais Repostos',
        xaxis_title='Quantidade',
        height=340, margin=dict(l=280, r=40, t=52, b=44),
    )
    return _render(fig)


# ── 9. Motivos de reposição ───────────────────────────────────────────────────
def gerar_grafico_motivo_reposicao(df):
    if 'Justificativa' not in df.columns:
        return None
    serie = (df['Justificativa'].dropna().astype(str).str.strip()
             .replace('', pd.NA).dropna())
    if serie.empty:
        return None
    top = serie.value_counts().nlargest(10).reset_index()
    top.columns = ['Motivo', 'Qtd']
    top = top.sort_values('Qtd')

    fig = go.Figure(go.Bar(
        x=top['Qtd'], y=top['Motivo'], orientation='h',
        marker_color=_PURPLE,
        text=top['Qtd'], textposition='outside',
        hovertemplate='%{y}: %{x}<extra></extra>',
    ))
    fig.update_layout(
        title='Top 10 Motivos de Reposição',
        xaxis_title='Quantidade',
        height=max(300, len(top) * 38),
        margin=dict(l=230, r=40, t=52, b=44),
    )
    return _render(fig)
