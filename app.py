from flask import Flask, render_template_string, request, send_file, flash, redirect, url_for
import pandas as pd
import io
from processador import gerar_relatorio, gerar_pdf_canceladas_devolvidas, gerar_pdf_limbo
from graficos import gerar_grafico_comparativo
from datetime import datetime
from pathlib import Path
import sys
import os

# Aumenta limites do sistema operacional para aceitar requisições grandes
os.environ['WERKZEUG_MAX_CONTENT_LENGTH'] = '0'  # 0 = sem limite

# Navbar comum para todas as páginas
_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
<style>
:root{--bg:#f1f5f9;--surface:#fff;--border:#e2e8f0;--text:#1e293b;--muted:#64748b;
  --primary:#2563eb;--primary-h:#1d4ed8;--success:#16a34a;--warn:#ca8a04;--danger:#dc2626;
  --radius:10px;--sh:0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.04);}
*{box-sizing:border-box;}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);font-size:.875rem;margin:0;}

/* Navbar */
.app-nav{background:#0f172a;border-bottom:1px solid rgba(255,255,255,.06);padding:.65rem 1.25rem;}
.nav-brand{color:#f8fafc!important;font-weight:700;font-size:.9375rem;display:flex;align-items:center;gap:.5rem;text-decoration:none;}
.nav-mark{background:var(--primary);color:#fff;width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.72rem;font-weight:800;flex-shrink:0;}
.app-nav .nav-link{color:#94a3b8!important;font-size:.8rem;font-weight:500;padding:.35rem .7rem;border-radius:6px;transition:color .12s,background .12s;}
.app-nav .nav-link:hover{color:#e2e8f0!important;background:rgba(255,255,255,.07);}
.app-nav .nav-link.active{color:#93c5fd!important;background:rgba(96,165,250,.12);}
.app-nav .navbar-toggler{border:0;color:#94a3b8;padding:0;}

/* Layout */
.page-wrap{max-width:1100px;margin:0 auto;padding:1.5rem 1.25rem;}
.page-header{margin-bottom:1.25rem;}
.page-header h1{font-size:1.25rem;font-weight:700;margin:0;}
.page-header p{color:var(--muted);margin:.2rem 0 0;font-size:.8rem;}

/* Card */
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--sh);overflow:hidden;margin-bottom:1rem;}
.card-hd{padding:.875rem 1.25rem;border-bottom:1px solid var(--border);font-weight:600;font-size:.8125rem;color:var(--text);display:flex;align-items:center;gap:.5rem;}
.card-hd i{color:var(--muted);}
.card-bd{padding:1.25rem;}

/* Section label */
.sec-label{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0 0 .75rem;}

/* Forms */
.form-label{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-bottom:.3rem;}
.form-control,.form-select{border:1.5px solid var(--border);border-radius:7px;font-size:.875rem;padding:.45rem .75rem;color:var(--text);transition:border-color .12s,box-shadow .12s;background:var(--surface);}
.form-control:focus,.form-select:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(37,99,235,.1);outline:none;}
.form-text{font-size:.75rem;color:var(--muted);margin-top:.3rem;}
textarea.form-control{resize:vertical;}

/* Buttons */
.btn{border-radius:7px;font-weight:500;font-size:.8125rem;padding:.45rem .875rem;border:none;transition:all .12s;cursor:pointer;display:inline-flex;align-items:center;gap:.35rem;}
.btn-primary{background:var(--primary);color:#fff;}
.btn-primary:hover{background:var(--primary-h);color:#fff;}
.btn-success{background:var(--success);color:#fff;}
.btn-success:hover{background:#15803d;color:#fff;}
.btn-warning{background:var(--warn);color:#fff;}
.btn-warning:hover{background:#a16207;color:#fff;}
.btn-secondary{background:#475569;color:#fff;}
.btn-secondary:hover{background:#334155;color:#fff;}
.btn-ghost{background:transparent;color:var(--muted);border:1.5px solid var(--border);}
.btn-ghost:hover{background:var(--bg);color:var(--text);border-color:var(--border);}
.btn-dark{background:#0f172a;color:#f8fafc;}
.btn-dark:hover{background:#1e293b;color:#f8fafc;}
.btn-lg{padding:.575rem 1.25rem;font-size:.9rem;}
.btn-sm{padding:.3rem .65rem;font-size:.75rem;}
.w-100{width:100%;}

/* Table */
.tbl{width:100%;border-collapse:collapse;font-size:.8125rem;}
.tbl th{background:#f8fafc;border-bottom:1.5px solid var(--border);padding:.55rem 1rem;font-size:.675rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);text-align:left;white-space:nowrap;}
.tbl td{padding:.7rem 1rem;border-bottom:1px solid var(--border);color:var(--text);vertical-align:middle;}
.tbl tbody tr:last-child td{border-bottom:none;}
.tbl tbody tr:hover td{background:#f8fafc;}
.tbl .row-total td{background:#eff6ff;font-weight:700;color:var(--primary);border-top:1.5px solid var(--border);}

/* Chips */
.chip{display:inline-flex;align-items:center;gap:3px;padding:.18rem .55rem;border-radius:20px;font-size:.6875rem;font-weight:600;line-height:1.4;}
.chip-green{background:#dcfce7;color:#15803d;}
.chip-yellow{background:#fef9c3;color:#854d0e;}
.chip-red{background:#fee2e2;color:#b91c1c;}
.chip-blue{background:#dbeafe;color:#1d4ed8;}
.chip-slate{background:#f1f5f9;color:#475569;}
.chip-purple{background:#ede9fe;color:#6d28d9;}
.chip-orange{background:#ffedd5;color:#9a3412;}

/* Alert */
.alert{border-radius:8px;border:none;font-size:.8125rem;padding:.7rem 1rem;}
.alert-info{background:#eff6ff;color:#1e40af;border-left:3px solid #60a5fa;}
.alert-warning{background:#fffbeb;color:#92400e;border-left:3px solid #fbbf24;}
.alert-success{background:#f0fdf4;color:#166534;border-left:3px solid #4ade80;}
.alert-danger{background:#fff1f2;color:#be123c;border-left:3px solid #f87171;}

/* PDV card */
.rep-card{background:var(--surface);border:1px solid var(--border);border-radius:9px;padding:1rem 1.25rem;margin-bottom:.75rem;transition:box-shadow .12s;}
.rep-card:hover{box-shadow:0 4px 12px rgba(0,0,0,.08);}
.rep-card .rep-field{font-size:.8rem;color:var(--muted);margin:.2rem 0;}
.rep-card .rep-value{color:var(--text);font-weight:500;}
.rep-card .rep-product{font-size:.875rem;font-weight:600;color:var(--text);margin:.35rem 0;}
.rep-card .rep-status{margin-top:.5rem;display:flex;flex-wrap:wrap;gap:.35rem;}
.rep-divider{border:none;border-top:1px solid var(--border);margin:.5rem 0;}

/* Status bar */
.stat-bar{background:var(--bg);border-radius:6px;overflow:hidden;height:6px;margin-top:4px;}
.stat-bar-fill{height:100%;border-radius:6px;background:var(--primary);}

/* Misc */
.text-muted{color:var(--muted)!important;}
.fw-600{font-weight:600;}
.gap-2{gap:.5rem!important;}
</style>"""

NAVBAR_HTML = r"""
<nav class="app-nav navbar navbar-expand-lg">
  <div class="container-fluid px-0">
    <a class="nav-brand navbar-brand" href="/">
      <div class="nav-mark">RS</div>
      Revalle Sisal
    </a>
    <button class="navbar-toggler app-nav" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
      <i class="bi bi-list fs-5"></i>
    </button>
    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav ms-auto gap-1">
        <li class="nav-item">
          <a class="nav-link {{ 'active' if page == 'dashboard' else '' }}" href="/">
            <i class="bi bi-bar-chart-line"></i> Gestão de Reposições
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link {{ 'active' if page == 'consulta' else '' }}" href="/consulta_pdv">
            <i class="bi bi-search"></i> Consultar PDV
          </a>
        </li>
        <li class="nav-item">
          <a class="nav-link {{ 'active' if page == 'importar' else '' }}" href="/importar_dados">
            <i class="bi bi-cloud-upload"></i> Importar Dados
          </a>
        </li>
      </ul>
    </div>
  </div>
</nav>
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Gestão de Reposições — Revalle Sisal</title>
""" + _CSS + """
</head>
<body>
""" + NAVBAR_HTML + r"""
<div class="page-wrap">

  <div class="page-header">
    <h1>Gestão de Reposições</h1>
    <p>Gere relatórios e compare períodos de entrega</p>
  </div>

  <!-- Alertas -->
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for message in messages %}
        <div class="alert alert-warning mb-3">{{ message }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <!-- Formulários lado a lado -->
  <div class="row g-3 mb-2">

    <!-- Filtro por período -->
    <div class="col-lg-6">
      <div class="card h-100">
        <div class="card-hd"><i class="bi bi-calendar-range"></i> Relatório por Período</div>
        <div class="card-bd">
          <form method="POST" action="/" class="row g-3">
            <input type="hidden" name="acao" value="relatorio">
            <div class="col-6">
              <label class="form-label">Data Início</label>
              <input type="date" class="form-control" name="data_inicio" required>
            </div>
            <div class="col-6">
              <label class="form-label">Data Fim</label>
              <input type="date" class="form-control" name="data_fim" required>
            </div>
            <div class="col-12">
              <button type="submit" class="btn btn-primary w-100">
                <i class="bi bi-bar-chart"></i> Gerar Relatório
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Comparar períodos -->
    <div class="col-lg-6">
      <div class="card h-100">
        <div class="card-hd"><i class="bi bi-arrow-left-right"></i> Comparar Dois Períodos</div>
        <div class="card-bd">
          <form method="POST" action="/comparar" class="row g-3">
            <div class="col-6">
              <label class="form-label">Mês 1</label>
              <select name="mes1" class="form-select" required>
                <option value="1">Janeiro</option><option value="2">Fevereiro</option>
                <option value="3">Março</option><option value="4">Abril</option>
                <option value="5">Maio</option><option value="6">Junho</option>
                <option value="7">Julho</option><option value="8">Agosto</option>
                <option value="9">Setembro</option><option value="10">Outubro</option>
                <option value="11">Novembro</option><option value="12">Dezembro</option>
              </select>
            </div>
            <div class="col-6">
              <label class="form-label">Ano 1</label>
              <input type="number" name="ano1" class="form-control" placeholder="2025" required>
            </div>
            <div class="col-6">
              <label class="form-label">Mês 2</label>
              <select name="mes2" class="form-select" required>
                <option value="1">Janeiro</option><option value="2">Fevereiro</option>
                <option value="3">Março</option><option value="4">Abril</option>
                <option value="5">Maio</option><option value="6">Junho</option>
                <option value="7">Julho</option><option value="8">Agosto</option>
                <option value="9">Setembro</option><option value="10">Outubro</option>
                <option value="11">Novembro</option><option value="12">Dezembro</option>
              </select>
            </div>
            <div class="col-6">
              <label class="form-label">Ano 2</label>
              <input type="number" name="ano2" class="form-control" placeholder="2026" required>
            </div>
            <div class="col-12">
              <button type="submit" class="btn btn-secondary w-100">
                <i class="bi bi-arrow-left-right"></i> Comparar
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

  </div>

  <!-- Resumo -->
  {% if dados %}
  <div class="card">
    <div class="card-hd"><i class="bi bi-clipboard-data"></i> Resumo do Período</div>
    <div class="card-bd">

      <div style="display:flex;flex-wrap:wrap;gap:1.5rem;margin-bottom:1rem;padding-bottom:1rem;border-bottom:1px solid var(--border);">
        {% if data_inicio and data_fim %}
        <div>
          <div style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);">Período</div>
          <div style="font-weight:600;margin-top:.15rem;">{{ data_inicio.strftime('%d/%m/%Y') }} — {{ data_fim.strftime('%d/%m/%Y') }}</div>
        </div>
        {% endif %}
        <div>
          <div style="font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);">Tempo médio lançamento → aprovação</div>
          <div style="font-weight:600;margin-top:.15rem;">
            {% if media_dias_entrega is not none %}{{ media_dias_entrega|round(1) }} dias{% else %}—{% endif %}
          </div>
        </div>
      </div>

      <div style="overflow-x:auto;">
        <table class="tbl">
          <thead>
            <tr><th>Descrição</th><th style="text-align:right">Quantidade</th><th style="text-align:right">Percentual</th></tr>
          </thead>
          <tbody>
            {% for chave, valores in dados.items() %}
            <tr {% if 'TOTAL' in chave %}class="row-total"{% endif %}>
              <td>{{ chave }}</td>
              <td style="text-align:right;font-variant-numeric:tabular-nums;">{{ valores[0] }}</td>
              <td style="text-align:right;font-variant-numeric:tabular-nums;">{{ valores[1] }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>

      <div style="display:flex;gap:.75rem;margin-top:1rem;flex-wrap:wrap;">
        <form method="POST" action="/pdf" target="_blank" style="flex:1;min-width:200px;">
          <input type="hidden" name="data_inicio" value="{{ request.form.get('data_inicio','') }}">
          <input type="hidden" name="data_fim" value="{{ request.form.get('data_fim','') }}">
          <button type="submit" class="btn btn-success w-100">
            <i class="bi bi-file-earmark-pdf"></i> PDF Canceladas/Devolvidas
          </button>
        </form>
        <form method="POST" action="/pdf_limbo" target="_blank" style="flex:1;min-width:200px;">
          <input type="hidden" name="data_inicio" value="{{ request.form.get('data_inicio','') }}">
          <input type="hidden" name="data_fim" value="{{ request.form.get('data_fim','') }}">
          <button type="submit" class="btn btn-warning w-100">
            <i class="bi bi-file-earmark-pdf"></i> PDF Limbo
          </button>
        </form>
      </div>

    </div>
  </div>
  {% endif %}

  <!-- Gráfico comparativo (rota /comparar) -->
  {% if grafico %}
  <div class="card"><div class="card-bd">{{ grafico | safe }}</div></div>
  {% endif %}

  <!-- === Seção de análises (gerada pela rota /) === -->
  {% if graficos %}

  <!-- 1. Evolução mensal — largura total -->
  {% if graficos.evolucao %}
  <div class="card"><div class="card-bd">{{ graficos.evolucao | safe }}</div></div>
  {% endif %}

  <!-- 2. Donut status + Dia da semana -->
  {% if graficos.donut or graficos.dia_semana %}
  <div class="row g-3">
    {% if graficos.donut %}
    <div class="col-lg-5">
      <div class="card h-100"><div class="card-bd">{{ graficos.donut | safe }}</div></div>
    </div>
    {% endif %}
    {% if graficos.dia_semana %}
    <div class="col-lg-7">
      <div class="card h-100"><div class="card-bd">{{ graficos.dia_semana | safe }}</div></div>
    </div>
    {% endif %}
  </div>
  {% endif %}

  <!-- 3. Top motoristas — clicável -->
  {% if graficos.motoristas %}
  <div class="card">
    <div class="card-bd">
      {{ graficos.motoristas | safe }}
      <p style="font-size:.75rem;color:var(--muted);margin:.4rem 0 0;">
        <i class="bi bi-hand-index"></i> Clique no motorista para ver detalhes abaixo.
      </p>
    </div>
  </div>
  <div id="detalhes-motorista" style="margin-bottom:.5rem;"></div>
  <script>
    window.FILTRO = {
      data_inicio: "{{ request.form.get('data_inicio','') }}",
      data_fim: "{{ request.form.get('data_fim','') }}"
    };
    (function(){
      const chartDiv = document.getElementById('grafico_motoristas');
      if(!chartDiv || !window.Plotly) return;
      chartDiv.on('plotly_click', function(ev){
        try{
          const p = ev.points && ev.points[0];
          if(!p) return;
          const nome = (p.y || p.x || '').toString();
          if(!nome) return;
          const di = window.FILTRO.data_inicio, df = window.FILTRO.data_fim;
          const url = `/detalhes_motorista?nome=${encodeURIComponent(nome)}&data_inicio=${encodeURIComponent(di)}&data_fim=${encodeURIComponent(df)}`;
          const alvo = document.getElementById('detalhes-motorista');
          alvo.innerHTML = "<div class='card'><div class='card-bd' style='display:flex;align-items:center;gap:.5rem;'><div class='spinner-border' role='status' style='width:1rem;height:1rem;border-width:2px;'></div> Carregando...</div></div>";
          fetch(url).then(r=>r.text()).then(html=>{alvo.innerHTML=html;}).catch(()=>{alvo.innerHTML="<div class='alert alert-danger'>Erro ao carregar detalhes.</div>";});
        }catch(e){console.error(e);}
      });
    })();
  </script>
  {% endif %}

  <!-- 4. Top produtos + Top PDVs -->
  {% if graficos.produtos or graficos.top_pdvs %}
  <div class="row g-3">
    {% if graficos.produtos %}
    <div class="col-lg-6">
      <div class="card h-100"><div class="card-bd">{{ graficos.produtos | safe }}</div></div>
    </div>
    {% endif %}
    {% if graficos.top_pdvs %}
    <div class="col-lg-6">
      <div class="card h-100"><div class="card-bd">{{ graficos.top_pdvs | safe }}</div></div>
    </div>
    {% endif %}
  </div>
  {% endif %}

  <!-- 5. Histograma tempo de aprovação -->
  {% if graficos.tempo %}
  <div class="card"><div class="card-bd">{{ graficos.tempo | safe }}</div></div>
  {% endif %}

  <!-- 6. Motivos de reposição -->
  {% if graficos.motivo %}
  <div class="card"><div class="card-bd">{{ graficos.motivo | safe }}</div></div>
  {% endif %}

  {% endif %}{# /graficos #}

</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

CONSULTA_PDV_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Consultar PDV — Revalle Sisal</title>
""" + _CSS + """
</head>
<body>
""" + NAVBAR_HTML + r"""
<div class="page-wrap">

  <div class="page-header">
    <h1>Consultar PDV</h1>
    <p>Busca rápida de reposições por código do PDV</p>
  </div>

  <!-- Alertas -->
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for message in messages %}
        <div class="alert alert-warning mb-3">{{ message }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <div class="card">
    <div class="card-hd"><i class="bi bi-search"></i> Busca por PDV</div>
    <div class="card-bd">
      <form method="POST" action="/consulta_pdv">
        <div style="display:flex;gap:.75rem;align-items:flex-end;flex-wrap:wrap;">
          <div style="flex:1;min-width:200px;">
            <label class="form-label">Código do PDV</label>
            <input type="number" class="form-control" id="pdv" name="pdv"
                   placeholder="Ex: 12345"
                   value="{{ pdv_consultado or '' }}" required autofocus
                   style="font-size:1rem;padding:.55rem .875rem;">
          </div>
          <button type="submit" class="btn btn-primary btn-lg">
            <i class="bi bi-search"></i> Consultar
          </button>
        </div>
      </form>
      <div class="alert alert-info" style="margin-top:1rem;margin-bottom:0;">
        <i class="bi bi-database"></i> Fonte: <strong>dados.csv</strong> importado —
        <a href="/importar_dados" style="color:inherit;font-weight:600;">atualizar base</a>
      </div>
    </div>
  </div>

  {% if resultado_pdv %}
  <div style="margin-top:1rem;">{{ resultado_pdv | safe }}</div>
  {% endif %}

</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

IMPORTAR_DADOS_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Importar Dados — Revalle Sisal</title>
""" + _CSS + """
</head>
<body>
""" + NAVBAR_HTML + r"""
<div class="page-wrap">

  <div class="page-header">
    <h1>Importar Dados</h1>
    <p>Cole o CSV de reposição para atualizar a base do sistema</p>
  </div>

  <!-- Status do arquivo -->
  {% if arquivo_atual %}
  <div class="alert alert-success" style="display:flex;align-items:center;gap:.6rem;margin-bottom:1rem;">
    <i class="bi bi-database-check" style="font-size:1.1rem;"></i>
    <span>
      <strong>Base ativa:</strong> {{ arquivo_atual }} &nbsp;·&nbsp;
      {{ arquivo_tamanho }} &nbsp;·&nbsp; importado em {{ arquivo_data }}
    </span>
  </div>
  {% else %}
  <div class="alert alert-warning" style="margin-bottom:1rem;">
    <i class="bi bi-exclamation-triangle"></i>
    Nenhum arquivo importado. Cole o CSV abaixo para começar.
  </div>
  {% endif %}

  <!-- Alertas flash -->
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for message in messages %}
        <div class="alert alert-{{ 'success' if message.startswith('✅') else 'danger' }}" style="margin-bottom:.75rem;">
          {{ message }}
        </div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <!-- Import textarea -->
  <div class="card">
    <div class="card-hd"><i class="bi bi-clipboard-data"></i> Colar CSV</div>
    <div class="card-bd">
      <form method="POST" action="/importar_dados" enctype="multipart/form-data">
        <input type="hidden" name="metodo" value="texto">
        <div style="margin-bottom:.875rem;">
          <label class="form-label">Conteúdo do arquivo</label>
          <textarea class="form-control" id="csv_texto" name="csv_texto"
                    rows="16" required
                    placeholder="Cole aqui o conteúdo do CSV..."
                    style="font-family:'JetBrains Mono','Fira Code','Courier New',monospace;font-size:.78rem;line-height:1.55;"></textarea>
          <div class="form-text">
            <i class="bi bi-info-circle"></i> Separadores aceitos: ponto-e-vírgula, vírgula ou tabulação
          </div>
        </div>
        <div style="display:flex;gap:.75rem;">
          <button type="button" class="btn btn-ghost btn-sm"
                  onclick="document.getElementById('csv_texto').value='';">
            <i class="bi bi-x"></i> Limpar
          </button>
          <button type="submit" class="btn btn-primary btn-lg" style="flex:1;">
            <i class="bi bi-cloud-upload"></i> Importar
          </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Consulta PDV após importação -->
  {% if arquivo_atual %}
  <div class="card" style="margin-top:1rem;">
    <div class="card-hd"><i class="bi bi-search"></i> Consultar PDV</div>
    <div class="card-bd">
      <form method="POST" action="/importar_dados">
        <input type="hidden" name="metodo" value="buscar_pdv">
        <div style="display:flex;gap:.75rem;align-items:flex-end;flex-wrap:wrap;">
          <div style="flex:1;min-width:180px;">
            <label class="form-label">Código do PDV</label>
            <input type="number" class="form-control" name="pdv"
                   placeholder="Ex: 12345"
                   value="{{ pdv_consultado or '' }}" required
                   style="font-size:1rem;padding:.55rem .875rem;">
          </div>
          <button type="submit" class="btn btn-dark btn-lg">
            <i class="bi bi-search"></i> Buscar
          </button>
        </div>
      </form>
      {% if resultado_pdv %}
      <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid var(--border);">
        {{ resultado_pdv | safe }}
      </div>
      {% endif %}
    </div>
  </div>
  {% endif %}

</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""





if getattr(sys, 'frozen', False):
  BASE_DIR = Path(sys.executable).parent
else:
  BASE_DIR = Path(__file__).resolve().parent

DADOS_CSV = BASE_DIR / "dados.csv"
PDF_SAIDA = BASE_DIR / "relatorio_canceladas_devolvidas.pdf"
PDF_LIMBO = BASE_DIR / "relatorio_limbo.pdf"

# ============================================================================
# Configuração para aceitar payloads grandes
# ============================================================================
import werkzeug.formparser

# Aumenta drasticamente os limites do Werkzeug
class LargeMultiPartParser(werkzeug.formparser.MultiPartParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_form_memory_size = 1024 * 1024 * 1024  # 1GB
        self.max_content_length = 1024 * 1024 * 1024    # 1GB

# Substitui o parser padrão
werkzeug.formparser.MultiPartParser = LargeMultiPartParser

# ============================================================================

app = Flask(__name__)
app.secret_key = "segredo"
# Remove limites do Flask
app.config['MAX_CONTENT_LENGTH'] = None
app.config['MAX_FORM_MEMORY_SIZE'] = 1024 * 1024 * 1024  # 1 GB
app.config['MAX_FORM_PARTS'] = 100000

# Middleware para garantir que não há limites nas requisições
@app.before_request
def before_request():
    """Remove limites antes de processar cada requisição."""
    if request.environ.get('CONTENT_LENGTH'):
        # Remove qualquer limite de tamanho
        pass  # Flask já está configurado sem limites


def _detectar_separador(texto):
    """Detecta o separador do CSV: tabulacao, ponto-e-virgula ou virgula."""
    primeira_linha = texto.splitlines()[0] if texto.strip() else ''
    if '\t' in primeira_linha:
        return '\t'
    if ';' in primeira_linha:
        return ';'
    return ','


def _consultar_pdv_no_df(df, id_grupo):
    """
    Recebe um DataFrame (de xlsx ou CSV) e retorna HTML com o histórico
    do PDV. Mapeamento por índice de coluna (mesmo do processador.py):
      C (2)=PDV | E (4)=Solicitação | G (6)=Data Lanç | I (8)=Status
      J (9)=DataAprov | N (13)=NF_Status | O (14)=CodProd
      P (15)=DescProd | Q (16)=Qtd | R (17)=Uni
    """
    if df.shape[1] < 18:
        return ("<div class='alert alert-warning'>A tabela informada tem menos de 18 colunas. "
                "Verifique se o CSV está completo e no formato correto esperado pelo sistema.</div>")

    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    df['_PDV']         = df.iloc[:, 2].astype(str).str.strip()
    df['_Solicitacao'] = df.iloc[:, 4].astype(str).str.strip()
    df['_DataLanc']    = pd.to_datetime(df.iloc[:, 6], errors='coerce', dayfirst=True)
    df['_Status']      = df.iloc[:, 8].astype(str).str.strip().str.lower()
    df['_DataAprov']   = pd.to_datetime(df.iloc[:, 9], errors='coerce', dayfirst=True)
    df['_NF_Status']   = df.iloc[:, 13].astype(str).str.strip().str.upper()
    df['_CodProduto']  = df.iloc[:, 14].astype(str).str.strip()
    df['_DescProduto'] = df.iloc[:, 15].astype(str).str.strip()
    def _fmt_qtd(v):
        try:
            return int(float(str(v).strip().replace(',', '.')))
        except (ValueError, TypeError):
            return str(v).strip()
    df['_Qtd'] = df.iloc[:, 16].apply(_fmt_qtd)
    df['_Uni']         = df.iloc[:, 17].astype(str).str.strip()

    registros = df[df['_PDV'] == str(id_grupo)].sort_values('_DataLanc', ascending=True)

    if registros.empty:
        return (f"<div class='alert alert-warning'>O PDV <strong>{id_grupo}</strong> "
                "não foi encontrado nos dados informados.</div>")

    html = (f"<p style='font-size:.8rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em;"
            f"color:#64748b;margin:0 0 .875rem;'>PDV {id_grupo} — {len(registros)} reposição(ões)</p>")

    for _, row in registros.iterrows():
        status        = row['_Status']
        data          = row['_DataLanc'].strftime('%d/%m/%Y') if pd.notna(row['_DataLanc']) else '—'
        data_aprov_dt = row['_DataAprov'] if pd.notna(row['_DataAprov']) else None
        data_aprovacao = data_aprov_dt.strftime('%d/%m/%Y') if data_aprov_dt is not None else '—'
        nf_status     = row['_NF_Status']
        produto       = row['_DescProduto']
        qtd           = row['_Qtd']
        uni           = row['_Uni']
        cod_produto   = row['_CodProduto']
        solicitacao   = row['_Solicitacao']

        if status == 'aprovada':
            s_chip = "<span class='chip chip-green'>Aprovada</span>"
            if nf_status == 'E':
                nf_chip = "<span class='chip chip-blue'>Entregue</span>"
            elif nf_status == 'D':
                nf_chip = "<span class='chip chip-orange'>Devolvida</span>"
            elif nf_status == 'C':
                nf_chip = "<span class='chip chip-red'>Cancelada</span>"
            else:
                if data_aprov_dt is not None:
                    dias = (datetime.now() - data_aprov_dt).days
                    nf_chip = ("<span class='chip chip-red'>Cancelada</span>" if dias > 5
                               else "<span class='chip chip-purple'>Aguardando entrega</span>")
                else:
                    nf_chip = "<span class='chip chip-purple'>Aguardando entrega</span>"
        elif status == 'pendente':
            s_chip  = "<span class='chip chip-yellow'>Pendente</span>"
            nf_chip = ""
        elif status == 'reprovada':
            s_chip  = "<span class='chip chip-red'>Reprovada</span>"
            nf_chip = ""
        else:
            s_chip  = f"<span class='chip chip-slate'>{status}</span>"
            nf_chip = ""

        html += f"""
        <div class='rep-card'>
          <div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;'>
            <div>
              <div class='rep-product'>{cod_produto} &mdash; {qtd} {uni} &mdash; {produto}</div>
              <div class='rep-status'>{s_chip}{nf_chip}</div>
            </div>
            <div style='text-align:right;flex-shrink:0;'>
              <div class='rep-field'>Solicitação <span class='rep-value'>#{solicitacao}</span></div>
            </div>
          </div>
          <hr class='rep-divider'>
          <div style='display:flex;gap:1.5rem;flex-wrap:wrap;'>
            <div class='rep-field'>Lançamento &nbsp;<span class='rep-value'>{data}</span></div>
            <div class='rep-field'>Aprovação &nbsp;<span class='rep-value'>{data_aprovacao}</span></div>
          </div>
        </div>
        """

    html += ("<div class='alert alert-info' style='margin-top:.5rem;'>"
             "Caso a reposição não esteja na lista acima, favor entrar em contato com o RN.</div>")
    return html


def verificar_autorizacao_web(id_grupo):
    """Lê dados.csv importado e consulta o PDV."""
    if not DADOS_CSV.exists():
        return "<div class='alert alert-warning'>Nenhum arquivo importado. Acesse <a href='/importar_dados'>Importar Dados</a> para carregar o CSV.</div>"
    try:
        for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
            try:
                with open(DADOS_CSV, 'r', encoding=enc) as f:
                    primeira_linha = f.readline()
                sep = ';' if ';' in primeira_linha else ('\t' if '\t' in primeira_linha else ',')
                df = pd.read_csv(DADOS_CSV, sep=sep, header=0, dtype=str, keep_default_na=False, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        return _consultar_pdv_no_df(df, id_grupo)
    except Exception as e:
        return f"<div class='alert alert-danger'>Erro ao ler dados: {e}</div>"


def verificar_autorizacao_csv(csv_texto, id_grupo):
    """Faz parse do texto CSV/TSV colado pelo usuário e consulta o PDV."""
    try:
        sep = _detectar_separador(csv_texto)
        df = pd.read_csv(io.StringIO(csv_texto), sep=sep, header=0,
                         dtype=str, keep_default_na=False)
        # Se o CSV não tiver cabeçalho suficiente (primeira linha parece dado)
        # tenta sem cabeçalho
        if df.shape[1] < 18:
            df = pd.read_csv(io.StringIO(csv_texto), sep=sep, header=None,
                             dtype=str, keep_default_na=False)
        return _consultar_pdv_no_df(df, id_grupo)
    except Exception as e:
        return f"<div class='alert alert-danger'>Erro ao processar CSV: {e}</div>"

def _render_dashboard(**extra):
    """Renderiza o dashboard passando sempre todos os parâmetros necessários."""
    defaults = dict(
        dados=None, graficos=None, grafico=None,
        media_dias_entrega=None, data_inicio=None, data_fim=None,
    )
    defaults.update(extra)
    return render_template_string(DASHBOARD_HTML, page='dashboard', **defaults)


@app.errorhandler(413)
def request_entity_too_large(_error):
    """Handler para erro 413 - Request Entity Too Large"""
    flash("⚠️ Arquivo ou texto muito grande. Tente: 1) Enviar arquivo menor, 2) Dividir o CSV em partes menores.")
    return render_template_string(IMPORTAR_DADOS_HTML, page='importar'), 413


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # ── Relatório por período ────────────────────────────────────────
        di   = request.form.get('data_inicio')
        dfim = request.form.get('data_fim')

        if not di or not dfim:
            flash("Informe Data Início e Data Fim para gerar o relatório.")
            return _render_dashboard()

        try:
            data_inicio = datetime.strptime(di, "%Y-%m-%d")
            data_fim    = datetime.strptime(dfim, "%Y-%m-%d")
        except ValueError:
            flash("Formato de data inválido.")
            return _render_dashboard()

        try:
            dados, graficos, media_dias_entrega = gerar_relatorio(data_inicio, data_fim)
        except FileNotFoundError:
            flash("Nenhum arquivo importado. Acesse 'Importar Dados' para carregar o CSV antes de gerar o relatório.")
            return _render_dashboard()

        return _render_dashboard(
            dados=dados, graficos=graficos,
            media_dias_entrega=media_dias_entrega,
            data_inicio=data_inicio, data_fim=data_fim,
        )

    return _render_dashboard()


@app.route('/consulta_pdv', methods=['GET', 'POST'])
def consulta_pdv():
    """Consulta simples de PDV no dados.xlsx."""
    if request.method == 'POST':
        pdv_raw = request.form.get('pdv', '').strip()

        if not pdv_raw or not pdv_raw.isdigit():
            flash("Por favor, informe um código de PDV válido (apenas números).")
            return render_template_string(CONSULTA_PDV_HTML, page='consulta')

        resultado_pdv = verificar_autorizacao_web(pdv_raw)
        return render_template_string(CONSULTA_PDV_HTML,
            resultado_pdv=resultado_pdv,
            pdv_consultado=pdv_raw,
            page='consulta',
        )

    return render_template_string(CONSULTA_PDV_HTML, page='consulta')


@app.route('/importar_dados', methods=['GET', 'POST'])
def importar_dados():
    """Rota para importar CSV de reposição (substitui dados.csv em disco)."""
    if request.method == 'POST':
        metodo = request.form.get('metodo', '')

        if metodo == 'texto':
            csv_texto = request.form.get('csv_texto', '').strip()
            if not csv_texto:
                flash("Por favor, cole o conteúdo CSV/TXT na área de texto.")
                return render_template_string(IMPORTAR_DADOS_HTML, page='importar', **_status_arquivo())

            try:
                DADOS_CSV.write_text(csv_texto, encoding='utf-8')
                sep = _detectar_separador(csv_texto)
                df = pd.read_csv(io.StringIO(csv_texto), sep=sep, header=0, dtype=str, keep_default_na=False)
                total_registros = len(df)
                pdvs_unicos = df.iloc[:, 2].astype(str).str.strip().nunique() if df.shape[1] > 2 else 0
                flash(f"✅ Dados importados com sucesso — {total_registros} registros, {pdvs_unicos} PDVs únicos.")
            except Exception as e:
                flash(f"Erro ao importar texto: {e}")
            return render_template_string(IMPORTAR_DADOS_HTML, page='importar', **_status_arquivo())

        elif metodo == 'buscar_pdv':
            pdv_raw = request.form.get('pdv', '').strip()
            if not pdv_raw or not pdv_raw.isdigit():
                flash("Por favor, informe um código de PDV válido (apenas números).")
                return render_template_string(IMPORTAR_DADOS_HTML, page='importar', **_status_arquivo())

            resultado_pdv = verificar_autorizacao_web(pdv_raw)
            return render_template_string(IMPORTAR_DADOS_HTML,
                page='importar',
                resultado_pdv=resultado_pdv,
                pdv_consultado=pdv_raw,
                **_status_arquivo(),
            )

    return render_template_string(IMPORTAR_DADOS_HTML, page='importar', **_status_arquivo())


def _status_arquivo():
    """Retorna dict com informações do arquivo de dados atual (csv ou xlsx)."""
    import datetime as dt
    for path in (DADOS_CSV,):
        if path.exists():
            stat = path.stat()
            tamanho_mb = stat.st_size / (1024 * 1024)
            modificado = dt.datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M')
            return dict(
                arquivo_atual=path.name,
                arquivo_tamanho=f"{tamanho_mb:.1f} MB",
                arquivo_data=modificado,
            )
    return dict(arquivo_atual=None, arquivo_tamanho=None, arquivo_data=None)


@app.route('/pdf', methods=['POST'])
def gerar_pdf():
    di = request.form.get('data_inicio')
    dfim = request.form.get('data_fim')

    if not di or not dfim:
        flash("Informe Data Início e Data Fim para gerar o PDF.")
        return redirect(url_for('index'))

    try:
        data_inicio = datetime.strptime(di, "%Y-%m-%d")
        data_fim = datetime.strptime(dfim, "%Y-%m-%d")
    except ValueError:
        flash("Formato de data inválido para o PDF.")
        return redirect(url_for('index'))

    try:
        gerar_pdf_canceladas_devolvidas(data_inicio, data_fim, str(PDF_SAIDA))
    except FileNotFoundError:
        flash("Nenhum arquivo importado. Acesse 'Importar Dados' para carregar o CSV.")
        return redirect(url_for('index'))
    return send_file(str(PDF_SAIDA), as_attachment=True)

@app.route('/pdf_limbo', methods=['POST'])
def pdf_limbo():
    di = request.form.get('data_inicio')
    dfim = request.form.get('data_fim')

    if not di or not dfim:
        flash("Informe Data Início e Data Fim para gerar o PDF de Limbo.")
        return redirect(url_for('index'))

    try:
        data_inicio = datetime.strptime(di, "%Y-%m-%d")
        data_fim = datetime.strptime(dfim, "%Y-%m-%d")
    except ValueError:
        flash("Formato de data inválido para o PDF de Limbo.")
        return redirect(url_for('index'))

    try:
        gerar_pdf_limbo(data_inicio, data_fim, str(PDF_LIMBO))
    except FileNotFoundError:
        flash("Nenhum arquivo importado. Acesse 'Importar Dados' para carregar o CSV.")
        return redirect(url_for('index'))
    return send_file(str(PDF_LIMBO), as_attachment=True)

@app.route('/comparar', methods=['GET', 'POST'])
def comparar():
    if request.method == 'GET':
        flash("Use o formulário para comparar dois períodos.")
        return redirect(url_for('index'))

    mes1 = request.form.get('mes1')
    ano1 = request.form.get('ano1')
    mes2 = request.form.get('mes2')
    ano2 = request.form.get('ano2')

    if not all([mes1, ano1, mes2, ano2]):
        flash("Preencha os dois períodos para comparar (mês e ano).")
        return redirect(url_for('index'))

    try:
        mes1 = int(mes1); ano1 = int(ano1)
        mes2 = int(mes2); ano2 = int(ano2)
    except ValueError:
        flash("Mês/Ano inválidos. Revise os valores.")
        return redirect(url_for('index'))

    if mes1 == mes2 and ano1 == ano2:
        flash("Escolha dois períodos diferentes para comparar.")
        return redirect(url_for('index'))

    if not DADOS_CSV.exists():
        flash("Nenhum arquivo importado. Acesse 'Importar Dados' para carregar o CSV.")
        return redirect(url_for('index'))

    from processador import _carregar_dados
    df = _carregar_dados()
    df.columns = df.columns.str.strip()
    df['Data_Lancamento'] = pd.to_datetime(df.iloc[:, 6], errors='coerce', dayfirst=True)
    df['Status'] = df.iloc[:, 8].astype(str).str.strip().str.lower()
    df['NF_Status'] = df.iloc[:, 13].astype(str).str.strip().str.upper()

    grafico_html = gerar_grafico_comparativo(df, mes1, ano1, mes2, ano2)

    return _render_dashboard(grafico=grafico_html)

# ===== Novo endpoint: detalhes por motorista =====
@app.route('/detalhes_motorista')
def detalhes_motorista():
    nome = request.args.get('nome', '').strip()
    di = request.args.get('data_inicio')
    dfim = request.args.get('data_fim')

    if not nome or not di or not dfim:
        return "<div class='alert alert-warning'>Parâmetros ausentes.</div>"

    try:
        data_inicio = datetime.strptime(di, "%Y-%m-%d")
        data_fim = datetime.strptime(dfim, "%Y-%m-%d")
    except ValueError:
        return "<div class='alert alert-warning'>Datas inválidas.</div>"

    if not DADOS_CSV.exists():
        return "<div class='alert alert-warning'>Nenhum arquivo importado. Acesse <a href='/importar_dados'>Importar Dados</a>.</div>"

    from processador import _carregar_dados
    df = _carregar_dados()
    df.columns = df.columns.str.strip()

    # Colunas usadas
    # G: Data_Lancamento (idx 6)
    # AI: Motorista (idx 34)
    # O: Código Produto (idx 14)
    # P: Descrição Produto (idx 15)
    # W: Justificativa (idx 22)
    df['Data_Lancamento'] = pd.to_datetime(df.iloc[:, 6], errors='coerce', dayfirst=True)
    df['Motorista'] = df.iloc[:, 34].astype(str).str.strip()
    df['CodProduto'] = df.iloc[:, 14].astype(str).str.strip()
    df['DescProduto'] = df.iloc[:, 15].astype(str).str.strip()
    df['Justificativa'] = df.iloc[:, 22].astype(str).str.strip()

    # Mesmo período aplicado no dashboard (Data de Lançamento)
    dfp = df[(df['Data_Lancamento'] >= data_inicio) & (df['Data_Lancamento'] <= data_fim)].copy()

    # Filtra pelo motorista clicado (case-insensitive)
    dfp = dfp[dfp['Motorista'].str.casefold() == nome.casefold()]

    if dfp.empty:
        return "<div class='card shadow-sm'><div class='card-body'><h5 class='mb-0'>Sem dados para este motorista no período selecionado.</h5></div></div>"

    # Top produtos (por descrição) - Top 5
    top_prod = (dfp.groupby('DescProduto')
                    .size()
                    .sort_values(ascending=False)
                    .head(5)
                    .reset_index(name='Quantidade'))

    # Motivos (justificativa) - Top 5
    top_motivos = (dfp.groupby('Justificativa')
                      .size()
                      .sort_values(ascending=False)
                      .head(5)
                      .reset_index(name='Quantidade'))

    # Totais para % e barras
    total_prod = int(top_prod['Quantidade'].sum()) if not top_prod.empty else 1
    total_mot = int(top_motivos['Quantidade'].sum()) if not top_motivos.empty else 1

    def _tabela_com_barras(df_tbl, titulo, total):
        if df_tbl.empty:
            return f"<div class='card mb-3 shadow-sm'><div class='card-body'><h5 class='mb-3'>{titulo}</h5><div class='text-muted'>Sem registros.</div></div></div>"
        linhas = ""
        for _, row in df_tbl.iterrows():
            desc = row.iloc[0]
            qnt = int(row['Quantidade'])
            pct = (qnt / total) * 100
            linhas += f"""
            <tr>
              <td style="min-width: 240px">{desc}</td>
              <td class="text-end" style="width: 110px">{qnt}</td>
              <td class="text-end" style="width: 100px">{pct:.1f}%</td>
            </tr>
            <tr>
              <td colspan="3">
                <div class="progress" style="height: 6px;">
                  <div class="progress-bar" role="progressbar" style="width:{pct:.0f}%;" aria-valuenow="{pct:.0f}" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
              </td>
            </tr>
            """
        return f"""
        <div class='card mb-3 shadow-sm'>
          <div class='card-body'>
            <h5 class='mb-3'>{titulo}</h5>
            <div class='table-responsive'>
              <table class='table table-sm align-middle mb-0'>
                <thead class='table-light'>
                  <tr><th>Descrição</th><th class='text-end'>Qtd</th><th class='text-end'>%</th></tr>
                </thead>
                <tbody>{linhas}</tbody>
              </table>
            </div>
          </div>
        </div>
        """

    html = ""
    html += _tabela_com_barras(top_prod, f"Principais Produtos Repostos — {nome}", total_prod)
    html += _tabela_com_barras(top_motivos, f"Motivos das Reposições — {nome}", total_mot)

    return html


if __name__ == '__main__':
    # Configurações para aceitar payloads grandes
    import werkzeug.serving
    
    # Remove todos os timeouts e limites
    werkzeug.serving.WSGIRequestHandler.protocol_version = "HTTP/1.1"
    
    # Aumenta o limite de linha de header (problema comum com payloads grandes)
    import http.server
    http.server.BaseHTTPRequestHandler._maxheaders = 0  # Remove limite de headers
    
    print("=" * 60)
    print("Servidor Flask iniciado com suporte a arquivos grandes")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True, threaded=True)
