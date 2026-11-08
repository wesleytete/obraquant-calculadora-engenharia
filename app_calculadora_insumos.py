"""ObraQuant 3.0 — calculadora demonstrativa de concreto e argamassa.
Executar: python -m streamlit run app_calculadora_insumos.py
Dependência: streamlit (python -m pip install streamlit)
"""
import csv
import math
from html import escape
from io import StringIO

import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="ObraQuant | Engenharia de Insumos",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Valores típicos apenas para pré-estimativa, não para dimensionamento.
SACO_KG = 50.0
MASSA_APARENTE_CIMENTO = 1440.0  # kg/m³ (aproximação)
FATORES_SECOS = {"Concreto": 1.54, "Argamassa": 1.33}
TRACOS = {
    "Concreto": {
        "1:2:3 · Convencional": (1.0, 2.0, 3.0),
        "1:1,5:3 · Rico em cimento": (1.0, 1.5, 3.0),
        "1:2:4 · Econômico em cimento": (1.0, 2.0, 4.0),
    },
    "Argamassa": {
        "1:3 · Rico em cimento": (1.0, 3.0, 0.0),
        "1:4 · Intermediário": (1.0, 4.0, 0.0),
        "1:5 · Menos cimento": (1.0, 5.0, 0.0),
    },
}
GEOMETRIAS = {
    "Concreto": {
        "Laje maciça": (("Largura", "Comprimento", "Espessura"), (4.0, 5.0, 0.12)),
        "Sapata": (("Largura", "Comprimento", "Altura"), (1.2, 1.2, 0.40)),
        "Viga baldrame": (("Largura", "Comprimento", "Altura"), (0.20, 5.0, 0.40)),
        "Pilar": (("Lado A", "Lado B", "Altura"), (0.30, 0.30, 3.0)),
        "Contrapiso": (("Largura", "Comprimento", "Espessura"), (4.0, 5.0, 0.07)),
    },
    "Argamassa": {
        "Reboco / emboço": (("Largura da parede", "Altura da parede", "Espessura"), (4.0, 2.8, 0.02)),
        "Contrapiso": (("Largura", "Comprimento", "Espessura"), (4.0, 5.0, 0.05)),
        "Regularização": (("Largura", "Comprimento", "Espessura"), (4.0, 5.0, 0.03)),
    },
}


def br(valor: float, casas: int = 2) -> str:
    """Formatação brasileira de números."""
    return f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def calcular(dimensoes, quantidade, perda, material, traco):
    """Cálculo geométrico seguido de estimativa por volumes secos e traço nominal."""
    bruto = math.prod(dimensoes) * quantidade
    planejado = bruto * (1 + perda / 100)
    seco = planejado * FATORES_SECOS[material]
    a, b, c = traco
    soma = a + b + c
    vc, va, vb = (seco * a / soma, seco * b / soma, seco * c / soma)
    kg = vc * MASSA_APARENTE_CIMENTO
    teorico = kg / SACO_KG
    return {
        "bruto": bruto, "planejado": planejado, "acrescimo": planejado - bruto,
        "seco": seco, "cimento_volume": vc, "areia": va, "brita": vb,
        "cimento_kg": kg, "sacos_teoricos": teorico,
        "sacos_compra": math.ceil(teorico - 1e-10),
        "quantidade_elementos": quantidade,
    }



def calcular_orcamento(r, material, preco_cimento, preco_areia, preco_brita,
                       mao_de_obra, frete, reserva_percentual):
    """Orçamento simplificado. Preços unitários definidos pelo usuário.

    O cimento é comprado em sacos inteiros; areia/brita são estimativas em m³.
    A reserva financeira incide sobre materiais + mão de obra + frete.
    """
    itens = [
        {"insumo": "Cimento (saco 50 kg)", "quantidade": r["sacos_compra"],
         "unidade": "saco", "preco": preco_cimento},
        {"insumo": "Areia (solta)", "quantidade": r["areia"],
         "unidade": "m³", "preco": preco_areia},
    ]
    if material == "Concreto":
        itens.append({"insumo": "Brita (solta)", "quantidade": r["brita"],
                      "unidade": "m³", "preco": preco_brita})
    for item in itens:
        item["total"] = item["quantidade"] * item["preco"]
    subtotal_materiais = sum(item["total"] for item in itens)
    base = subtotal_materiais + mao_de_obra + frete
    reserva_reais = base * reserva_percentual / 100
    total = base + reserva_reais
    return {
        "itens": itens, "materiais": subtotal_materiais,
        "mao_de_obra": mao_de_obra, "frete": frete,
        "reserva_reais": reserva_reais, "reserva_percentual": reserva_percentual,
        "total": total,
        "custo_m3": total / r["planejado"] if r["planejado"] > 0 else 0,
        "custo_unidade": total / max(1, r["quantidade_elementos"]),
    }


def exportar_orcamento_csv(material, elemento, nomes, dimensoes, quantidade,
                            perda, traco, r, orc):
    """CSV com UTF-8 BOM e delimitador ; para facilitar abertura no Excel."""
    arquivo = StringIO()
    w = csv.writer(arquivo, delimiter=";")
    w.writerow(["OBRAQUANT 3.1 | ORÇAMENTO PRELIMINAR"])
    w.writerow(["Material", material])
    w.writerow(["Elemento", elemento])
    for nome, medida in zip(nomes, dimensoes):
        w.writerow([f"{nome} (m)", br(medida, 3)])
    w.writerow(["Número de elementos", quantidade])
    w.writerow(["Traço nominal", traco])
    w.writerow(["Perdas de materiais (%)", perda])
    w.writerow(["Volume com perdas (m³)", br(r["planejado"], 3)])
    w.writerow([])
    w.writerow(["Item", "Quantidade", "Unidade", "Preço unitário (R$)", "Total (R$)"])
    for item in orc["itens"]:
        w.writerow([item["insumo"], br(item["quantidade"], 3), item["unidade"],
                    br(item["preco"], 2), br(item["total"], 2)])
    w.writerow(["Subtotal materiais", "", "", "", br(orc["materiais"], 2)])
    w.writerow(["Mão de obra", "", "valor global", "", br(orc["mao_de_obra"], 2)])
    w.writerow(["Frete", "", "valor global", "", br(orc["frete"], 2)])
    w.writerow([f"Reserva financeira ({br(orc['reserva_percentual'], 1)}%)", "", "", "",
                br(orc["reserva_reais"], 2)])
    w.writerow(["TOTAL", "", "", "", br(orc["total"], 2)])
    w.writerow(["Custo por m³ planejado", "", "R$/m³", "", br(orc["custo_m3"], 2)])
    w.writerow([])
    w.writerow(["Observação", "Preços são informados pelo usuário; não são cotações reais."])
    w.writerow(["Escopo", "Não inclui formas, armaduras, equipamentos, tributos, BDI ou demais insumos."])
    return ("\ufeff" + arquivo.getvalue()).encode("utf-8")


def exportar_csv(material, elemento, nomes, dimensoes, quantidade, perda, traco, r):
    arquivo = StringIO()
    w = csv.writer(arquivo, delimiter=";")
    w.writerow(["OBRAQUANT 3.1 - RESUMO DE INSUMOS"])
    w.writerow(["Tipo", material])
    w.writerow(["Elemento", elemento])
    for nome, medida in zip(nomes, dimensoes):
        w.writerow([f"{nome} (m)", br(medida, 3)])
    w.writerow(["Quantidade de elementos", quantidade])
    w.writerow(["Traço volumétrico", traco])
    w.writerow(["Perdas (%)", perda])
    w.writerow(["Volume geométrico (m³)", br(r["bruto"], 3)])
    w.writerow(["Volume planejado (m³)", br(r["planejado"], 3)])
    w.writerow([])
    w.writerow(["INSUMO", "QUANTIDADE", "UNIDADE"])
    w.writerow(["Cimento", r["sacos_compra"], "sacos de 50 kg"])
    w.writerow(["Cimento teórico", br(r["cimento_kg"], 2), "kg"])
    w.writerow(["Areia", br(r["areia"], 3), "m³ de material solto"])
    if material == "Concreto":
        w.writerow(["Brita", br(r["brita"], 3), "m³ de material solto"])
    w.writerow([])
    w.writerow(["AVISO", "Estimativa preliminar; traço nominal não determina fck."])
    return ("\ufeff" + arquivo.getvalue()).encode("utf-8")


def bloco_metricas(titulo, valor, legenda, icone, destaque=False):
    klass = "kpi kpi--accent" if destaque else "kpi"
    st.markdown(
        f'<div class="{klass}"><div class="kpi__top"><span>{escape(icone)} {escape(titulo)}</span>'
        f'<span class="kpi__dot"></span></div><div class="kpi__value">{escape(valor)}</div>'
        f'<div class="kpi__caption">{escape(legenda)}</div></div>',
        unsafe_allow_html=True,
    )


# Uma única paleta escura coerente com o VS Code/browser e com os formulários.
st.markdown("""
<style>
:root {color-scheme:dark;}
html, body, [data-testid="stAppViewContainer"], .stApp {background:#0b1120!important;color:#e7eef9!important;}
[data-testid="stHeader"] {background:rgba(11,17,32,.92)!important;}
[data-testid="stSidebar"] {background:#101a2d!important;border-right:1px solid #24354e;}
[data-testid="stSidebar"] * {color:#e4ecf8;}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {color:#c9d6e9!important;}
[data-testid="stMainBlockContainer"], .block-container {max-width:1300px;padding-top:1.6rem;padding-bottom:4rem;}
section[data-testid="stSidebar"] .block-container {padding-top:1.6rem;}
h1,h2,h3,p,span,label {letter-spacing:normal;}
h1,h2,h3 {color:#f4f8ff!important;}
[data-testid="stMarkdownContainer"] p {color:#d6e0ed;}
[data-testid="stCaptionContainer"] p {color:#9badc5!important;}
[data-testid="stWidgetLabel"] p {color:#d7e5f5!important;}
[data-testid="stRadio"] label p {color:#e5eefc!important;}
[data-testid="stAlert"] p {color:inherit!important;}
[data-testid="stExpander"] {border:1px solid #2a3c55!important;border-radius:12px!important;background:#111d30!important;}
[data-testid="stExpander"] summary {color:#eef4fd!important;}
[data-testid="stTable"], [data-testid="stDataFrame"] {border-radius:12px;overflow:hidden;}
div[data-baseweb="select"] > div, [data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {background:#18263c!important;color:#fff!important;border-color:#334761!important;}
[data-testid="stNumberInput"] button {background:#18263c!important;color:#fff!important;}
[data-testid="stSelectbox"] svg {fill:#d7e5f5!important;}
[data-testid="stSlider"] [role="slider"] {background:#36d0ac!important;border-color:#36d0ac!important;}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:.6rem;}
[data-testid="stTabs"] button[role="tab"] {color:#bfd0e6!important;}
[data-testid="stTabs"] button[aria-selected="true"] {color:#50e2b7!important;}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:#50e2b7!important;}
[data-testid="stDownloadButton"] button {background:#37cda7!important;color:#061c26!important;border:0!important;font-weight:750!important;border-radius:10px!important;}
[data-testid="stDownloadButton"] button:hover {background:#67eac8!important;}
hr {border-color:#2b3a51!important;}
.obra-head {display:flex;justify-content:space-between;align-items:center;gap:1rem;margin-bottom:1.4rem;}
.obra-brand {font-size:1.18rem;font-weight:850;color:#f0f7ff;letter-spacing:-.025em;}
.obra-brand b {color:#4be0b7;}
.obra-tag {border:1px solid #34536b;color:#95ead6;border-radius:99px;padding:.35rem .72rem;font-size:.73rem;font-weight:750;letter-spacing:.06em;white-space:nowrap;}
.hero {position:relative;overflow:hidden;background:linear-gradient(120deg,#142e45,#124b56 85%);border:1px solid #27546a;border-radius:22px;padding:2.15rem 2.2rem;margin-bottom:1.7rem;box-shadow:0 14px 35px rgba(0,0,0,.16);}
.hero:after {content:"";position:absolute;width:270px;height:270px;border-radius:50%;right:-80px;top:-100px;background:radial-gradient(circle,rgba(73,231,185,.2),transparent 70%);}
.hero .eyebrow {font-size:.75rem;color:#82f3d0;font-weight:850;letter-spacing:.14em;}
.hero h1 {font-size:clamp(1.7rem,3.5vw,2.9rem)!important;line-height:1.12;margin:.6rem 0 .65rem!important;letter-spacing:-.04em;}
.hero p {font-size:1rem;color:#c9dfeb!important;max-width:740px;line-height:1.6;}
.section-title {font-size:1.14rem;font-weight:800;color:#f3f7ff;margin:1.5rem 0 1rem;}
.section-title span {color:#54dfbc;}
.meta {display:flex;gap:.5rem;flex-wrap:wrap;margin-top:-.2rem;margin-bottom:1rem;}
.meta span {background:#17253a;color:#aabfd7;padding:.32rem .7rem;border:1px solid #283a52;border-radius:40px;font-size:.77rem;}
.kpi {background:linear-gradient(180deg,#16243a,#111c2e);border:1px solid #293c56;border-radius:17px;min-height:156px;padding:1.1rem 1.25rem;margin-bottom:1rem;box-shadow:0 8px 20px rgba(0,0,0,.1);}
.kpi--accent {border-color:#278c7c;background:linear-gradient(140deg,#133a40,#12303b);}
.kpi__top {display:flex;justify-content:space-between;gap:.6rem;color:#adbed4;font-weight:670;font-size:.82rem;}
.kpi__dot {width:7px;height:7px;border-radius:50%;background:#46ddba;flex-shrink:0;margin-top:.4rem;}
.kpi__value {font-weight:840;letter-spacing:-.05em;font-size:clamp(1.65rem,2.5vw,2.45rem);color:#f6fbff;margin:.85rem 0 .3rem;line-height:1.05;}
.kpi--accent .kpi__value {color:#69f0cd;}
.kpi__caption {color:#93a9c4;font-size:.76rem;}
.note {border:1px solid #245947;background:#12342f;color:#baf6df;border-radius:12px;padding:.85rem 1rem;font-size:.88rem;margin:.1rem 0 1.3rem;}
.side-title {font-weight:850;color:#f5f9ff;font-size:1.15rem;margin:0 0 .25rem;}
.side-sub {color:#8da4be;font-size:.8rem;margin-bottom:1.4rem;}
.side-divider {height:1px;background:#2b3c52;margin:1.1rem 0;}
.side-step {font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:#4be0b7;font-weight:850;margin:.3rem 0 1rem;}
 .budget-help {color:#9eb7ca;font-size:.85rem;line-height:1.5;margin-bottom:.8rem;}
[data-testid="stNumberInput"] input:focus {border-color:#4be0b7!important;box-shadow:0 0 0 1px #4be0b7!important;}
.foot {color:#839ab4;text-align:center;font-size:.78rem;margin-top:1.2rem;}
@media(max-width:700px){.hero{padding:1.35rem}.obra-tag{display:none}.kpi{min-height:135px}.obra-head{margin-bottom:.8rem}}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="side-title">⚙️ Configurar projeto</div><div class="side-sub">Os resultados são atualizados automaticamente.<br>Projeto de Wesley Goes Correa</div>', unsafe_allow_html=True)
    st.markdown('<div class="side-step">01 · Material e elemento</div>', unsafe_allow_html=True)
    material = st.radio("Tipo de material", ["Concreto", "Argamassa"], horizontal=True)
    elemento = st.selectbox("Elemento construtivo", list(GEOMETRIAS[material]))
    st.markdown('<div class="side-divider"></div><div class="side-step">02 · Dimensões</div>', unsafe_allow_html=True)
    unidade = st.segmented_control("Unidade de medida", ["m", "cm"], default="m")
    # Para Streamlit antigo: substitua st.segmented_control por st.radio(..., horizontal=True)
    nomes, padroes = GEOMETRIAS[material][elemento]
    fator = 100 if unidade == "cm" else 1
    dims = []
    for i, (nome, padrao) in enumerate(zip(nomes, padroes)):
        valor = st.number_input(
            f"{nome} ({unidade})", min_value=0.001 if unidade == "m" else 0.1,
            value=round(padrao * fator, 3 if unidade == "m" else 1),
            step=0.01 if unidade == "m" else 0.5,
            format="%.3f" if unidade == "m" else "%.1f",
            key=f"v2_{material}_{elemento}_{unidade}_{i}",
        )
        dims.append(valor / fator)
    qtd = st.number_input("Quantidade de elementos iguais", min_value=1, value=1, step=1)
    st.markdown('<div class="side-divider"></div><div class="side-step">03 · Dosagem estimada</div>', unsafe_allow_html=True)
    escolha = st.selectbox("Traço volumétrico", list(TRACOS[material]))
    traco = TRACOS[material][escolha]
    perda = st.slider("Perdas previstas (%)", min_value=0, max_value=15, value=5, step=1)
    st.caption("Traço por volume; não é especificação de fck.")
    st.markdown('<div class="side-divider"></div><div class="side-step">04 · Orçamento financeiro</div>', unsafe_allow_html=True)
    st.caption("Valores ilustrativos iniciais, **não** são preços pesquisados. Substitua pelas cotações reais.")
    preco_cimento = st.number_input("Preço do cimento (R$/saco de 50 kg)", min_value=0.0,
                                   value=42.0, step=1.0, format="%.2f", key="preco_cimento")
    preco_areia = st.number_input("Preço da areia (R$/m³)", min_value=0.0,
                                 value=165.0, step=5.0, format="%.2f", key="preco_areia")
    preco_brita = 0.0
    if material == "Concreto":
        preco_brita = st.number_input("Preço da brita (R$/m³)", min_value=0.0,
                                     value=195.0, step=5.0, format="%.2f", key="preco_brita")
    incluir_extras = st.toggle("Incluir mão de obra e frete", value=False)
    mao_de_obra = frete = 0.0
    if incluir_extras:
        mao_de_obra = st.number_input("Mão de obra total (R$)", min_value=0.0,
                                     value=0.0, step=50.0, format="%.2f")
        frete = st.number_input("Frete total (R$)", min_value=0.0,
                               value=0.0, step=25.0, format="%.2f")
    reserva_financeira = st.slider("Reserva financeira adicional (%)", 0, 20, 0,
                                  help="Reserva sobre materiais + mão de obra + frete. É diferente da perda física aplicada ao volume.")

r = calcular(dims, qtd, perda, material, traco)
orc = calcular_orcamento(r, material, preco_cimento, preco_areia, preco_brita,
                        mao_de_obra, frete, reserva_financeira)

st.markdown('<div class="obra-head"><div class="obra-brand">◈ OBRA<b>QUANT</b> <span style="color:#92a8c0;font-size:.72rem;font-weight:500">/ 3.1</span></div><div class="obra-tag">● PRÉ-ORÇAMENTO TÉCNICO</div></div>', unsafe_allow_html=True)
st.markdown('''<div class="hero"><div class="eyebrow">ENGENHARIA • PLANEJAMENTO • PRODUTIVIDADE</div><h1>Insumos calculados.<br>Decisões mais claras.</h1><p>Estime cimento, areia e brita para seus serviços. Ajuste as medidas à esquerda e acompanhe os quantitativos instantaneamente.</p></div>''', unsafe_allow_html=True)

st.markdown('<div class="section-title">01 <span>/</span> Visão geral do serviço</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="meta">' + ''.join(
        f'<span>{escape(v)}</span>' for v in [material, elemento, f"{qtd} unidade(s)", escolha.split(" · ")[0], f"{perda}% de perdas"]
    ) + '</div>', unsafe_allow_html=True
)
c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    bloco_metricas("Volume geométrico", f"{br(r['bruto'], 3)} m³", "Antes de acrescentar perdas", "▱")
with c2:
    bloco_metricas("Volume de planejamento", f"{br(r['planejado'], 3)} m³", "Quantidade líquida + reserva", "◈", True)
with c3:
    bloco_metricas("Reserva de perdas", f"{br(r['acrescimo'], 3)} m³", f"Margem definida: {perda}%", "↗")

st.markdown('<div class="section-title">02 <span>/</span> Insumos necessários</div>', unsafe_allow_html=True)
colunas = st.columns(3 if material == "Concreto" else 2, gap="medium")
with colunas[0]:
    bloco_metricas("Cimento · sacos de 50 kg", f"{r['sacos_compra']} sacos", f"Consumo teórico: {br(r['cimento_kg'], 1)} kg", "▣", True)
with colunas[1]:
    bloco_metricas("Areia · volume solto", f"{br(r['areia'], 3)} m³", "Volume estimado para fornecimento", "▤")
if material == "Concreto":
    with colunas[2]:
        bloco_metricas("Brita · volume solto", f"{br(r['brita'], 3)} m³", "Volume estimado para fornecimento", "⬡")

st.markdown('<div class="note">✓ Quantitativo atualizado. Utilize como estimativa preliminar e confira as premissas antes de comprar.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">03 <span>/</span> Orçamento preliminar</div>', unsafe_allow_html=True)
st.caption("Preço unitário e quantidade podem ser ajustados na barra lateral; os valores abaixo atualizam automaticamente.")
b1, b2, b3 = st.columns(3, gap="medium")
with b1:
    bloco_metricas("Subtotal dos materiais", f"R$ {br(orc['materiais'])}",
                   "Cimento em sacos inteiros", "▣")
with b2:
    bloco_metricas("Total estimado", f"R$ {br(orc['total'])}",
                   "Inclui adicionais selecionados", "◆", True)
with b3:
    bloco_metricas("Custo por m³ planejado", f"R$ {br(orc['custo_m3'])}",
                   "Total ÷ volume com perdas", "◈")


# ================================================================
# 05 · Dashboard analítico interativo (Plotly)
# ================================================================
# Todo o gráfico de composição usa m³: o cimento é mostrado em
# volume aparente, e NÃO em sacos (unidades incompatíveis).
st.markdown(
    '<div class="section-title">04 <span>/</span> Dashboard analítico</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Explore a composição volumétrica dos insumos e compare cenários "
    "de perdas. Passe o mouse sobre os gráficos para obter detalhes."
)

PALETA_INSUMOS = {"Cimento": "#52e4bd", "Areia": "#e3af62", "Brita": "#7a9ed0"}
COR_TEXTO = "#e7eef9"
COR_MUTED = "#a8bad0"
COR_GRADE = "rgba(142,164,194,.17)"
COR_FUNDO = "rgba(0,0,0,0)"

c_donut, c_barras = st.columns(2, gap="large")

with c_donut:
    st.markdown("**Composição dos insumos por volume**")
    partes_volume = {
        "Cimento": r["cimento_volume"],
        "Areia": r["areia"],
    }
    if material == "Concreto":
        partes_volume["Brita"] = r["brita"]

    labels = list(partes_volume)
    valores = list(partes_volume.values())
    grafico_rosca = go.Figure(
        go.Pie(
            labels=labels,
            values=valores,
            hole=0.67,
            sort=False,
            direction="clockwise",
            marker=dict(
                colors=[PALETA_INSUMOS[nome] for nome in labels],
                line=dict(color="#0b1120", width=3),
            ),
            textinfo="percent",
            textposition="inside",
            textfont=dict(size=13, color="#0b1120"),
            hovertemplate=(
                "<b>%{label}</b><br>Volume: %{value:.3f} m³"
                "<br>Proporção: %{percent}<extra></extra>"
            ),
        )
    )
    grafico_rosca.add_annotation(
        x=0.5, y=0.51,
        text=(f"<b>{br(r['seco'], 3)} m³</b><br>"
              "<span style='font-size:11px'>vol. seco estimado</span>"),
        showarrow=False,
        font=dict(size=18, color=COR_TEXTO),
        align="center",
    )
    grafico_rosca.update_layout(
        template="plotly_dark",
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor=COR_FUNDO,
        font=dict(color=COR_TEXTO, family="Arial"),
        legend=dict(
            orientation="h", yanchor="top", y=-0.09,
            xanchor="center", x=0.5,
            font=dict(color=COR_MUTED, size=12),
        ),
        margin=dict(l=12, r=12, t=12, b=48),
        height=335,
        showlegend=True,
    )
    st.plotly_chart(
        grafico_rosca,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="dashboard_insumos_rosca",
    )
    st.caption(
        "Proporções do traço em volumes aparentes de materiais secos "
        "e soltos. Os sacos de cimento são calculados separadamente."
    )

with c_barras:
    st.markdown("**Impacto das perdas no volume planejado**")
    cenarios = [5, 10, 15]
    volumes_cenarios = [r["bruto"] * (1 + p / 100) for p in cenarios]
    adicionais = [v - r["bruto"] for v in volumes_cenarios]
    cores_cenarios = ["#52e4bd" if p == perda else "#5687ba" for p in cenarios]
    grafico_barras = go.Figure()
    grafico_barras.add_trace(
        go.Bar(
            x=[f"{p}%" for p in cenarios],
            y=volumes_cenarios,
            marker=dict(color=cores_cenarios, line=dict(width=0)),
            customdata=list(zip(cenarios, adicionais)),
            text=[f"{br(v, 3)} m³" for v in volumes_cenarios],
            textposition="outside",
            textfont=dict(color=COR_TEXTO, size=12),
            hovertemplate=(
                "<b>Perdas: %{customdata[0]}%</b><br>"
                "Volume planejado: %{y:.3f} m³<br>"
                "Acréscimo: %{customdata[1]:.3f} m³"
                "<extra></extra>"
            ),
            name="Volume planejado",
        )
    )
    grafico_barras.add_hline(
        y=r["bruto"], line_dash="dot", line_color="#e3af62",
        annotation_text="Sem perdas", annotation_position="bottom right",
        annotation_font_color="#e3af62",
    )
    grafico_barras.update_layout(
        template="plotly_dark",
        paper_bgcolor=COR_FUNDO,
        plot_bgcolor=COR_FUNDO,
        height=335,
        margin=dict(l=12, r=14, t=24, b=30),
        showlegend=False,
        font=dict(color=COR_TEXTO, family="Arial"),
        xaxis=dict(title=None, showgrid=False, tickfont=dict(color=COR_MUTED)),
        yaxis=dict(
            title="Volume (m³)",
            title_font=dict(color=COR_MUTED, size=12),
            tickfont=dict(color=COR_MUTED),
            gridcolor=COR_GRADE,
            zeroline=False,
            rangemode="tozero",
            range=[0, max(volumes_cenarios) * 1.17],
        ),
        bargap=0.38,
    )
    st.plotly_chart(
        grafico_barras,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
        key="dashboard_perdas_barras",
    )
    st.caption(
        f"Volume base: {br(r['bruto'], 3)} m³. "
        f"Perda atualmente selecionada: {perda}%. "
        "A barra verde indica o cenário selecionado, quando for 5%, 10% ou 15%."
    )

st.markdown(
    '<div class="note">◈ Gráficos atualizados automaticamente quando você '
    'altera dimensões, quantidades, traço ou perdas na barra lateral.</div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["💰 Orçamento", "📋 Materiais", "📈 Gráficos", "📐 Memorial"])
with tab1:
    st.markdown("#### Composição do orçamento")
    linhas_orc = [
        {"Item": x["insumo"], "Quantidade": br(x["quantidade"], 3),
         "Unidade": x["unidade"], "Preço unitário (R$)": br(x["preco"]),
         "Total (R$)": br(x["total"])}
        for x in orc["itens"]
    ]
    st.dataframe(linhas_orc, hide_index=True, use_container_width=True)
    c_a, c_b = st.columns(2)
    with c_a:
        st.markdown(f"**Materiais:** R$ {br(orc['materiais'])}")
        st.markdown(f"**Mão de obra:** R$ {br(orc['mao_de_obra'])}")
        st.markdown(f"**Frete:** R$ {br(orc['frete'])}")
    with c_b:
        st.markdown(f"**Reserva adicional ({reserva_financeira}%):** R$ {br(orc['reserva_reais'])}")
        st.markdown(f"### Total: R$ {br(orc['total'])}")
        st.caption(f"Custo por elemento: R$ {br(orc['custo_unidade'])}")
    st.download_button(
        "⬇️ Exportar orçamento completo (CSV)",
        data=exportar_orcamento_csv(material, elemento, nomes, dims, qtd, perda, escolha, r, orc),
        file_name="obraquant_orcamento.csv", mime="text/csv", type="primary",
    )
    st.info("Preços iniciais são **exemplos editáveis**, não cotações de mercado. O orçamento é parcial: "
            "não inclui formas, armaduras, equipamentos, impostos, BDI nem demais serviços.")
with tab2:
    st.markdown("#### Resumo para o canteiro")
    tabela = [
        {"Insumo": "Cimento", "Quantidade": str(r["sacos_compra"]), "Unidade": "sacos de 50 kg"},
        {"Insumo": "Areia", "Quantidade": br(r["areia"], 3), "Unidade": "m³ (solta)"},
    ]
    if material == "Concreto":
        tabela.append({"Insumo": "Brita", "Quantidade": br(r["brita"], 3), "Unidade": "m³ (solta)"})
    st.dataframe(tabela, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Exportar quantitativos (CSV)",
        data=exportar_csv(material, elemento, nomes, dims, qtd, perda, escolha, r),
        file_name="obraquant_quantitativos.csv", mime="text/csv", type="primary",
    )
    st.caption("Sacos de cimento arredondados para cima. Outros volumes não incluem arredondamento comercial.")

with tab3:
    st.markdown("#### Composição volumétrica dos materiais secos")
    st.caption("Compare volumes dos componentes na mesma unidade (m³); não compare sacos com m³.")
    volumes = {"Cimento (volume aparente)": r["cimento_volume"], "Areia": r["areia"]}
    if material == "Concreto":
        volumes["Brita"] = r["brita"]
    try:
        import pandas as pd
        dados = pd.DataFrame({"Material": list(volumes), "Volume (m³)": list(volumes.values())})
        st.bar_chart(dados.set_index("Material"), color="#4be0b7", horizontal=True)
    except ImportError:
        for nome, vol in volumes.items():
            st.write(f"**{nome}:** {br(vol, 3)} m³")
            st.progress(min(1.0, vol / max(volumes.values())))
    st.info(f"O volume geométrico é {br(r['bruto'], 3)} m³; com {perda}% de perdas, o planejamento usa {br(r['planejado'], 3)} m³.")

    st.markdown("#### Distribuição de custos")
    partes = {x["insumo"]: x["total"] for x in orc["itens"]}
    if orc["mao_de_obra"]: partes["Mão de obra"] = orc["mao_de_obra"]
    if orc["frete"]: partes["Frete"] = orc["frete"]
    if orc["reserva_reais"]: partes["Reserva financeira"] = orc["reserva_reais"]
    if orc["total"] > 0:
        for nome, custo in partes.items():
            st.write(f"**{nome}** — R$ {br(custo)} · {br(custo/orc['total']*100,1)}%")
            st.progress(min(1., custo/orc["total"]))
    else:
        st.info("Insira valores positivos para visualizar a composição de custos.")

with tab4:
    st.markdown("#### Método de cálculo")
    st.latex(r"V_{geom} = d_1 \times d_2 \times d_3 \times N")
    st.latex(r"V_{plan} = V_{geom} \times (1 + p/100)")
    st.latex(r"V_{seco} = V_{plan} \times f")
    st.latex(r"V_i = V_{seco} \times \frac{p_i}{\sum p_i}")
    st.latex(r"S_{cimento} = \left\lceil \frac{V_{cimento} \times \rho_{ap}}{50} \right\rceil")
    st.write(
        f"Volume geométrico: **{br(r['bruto'], 3)} m³** · "
        f"Volume com perdas: **{br(r['planejado'], 3)} m³** · "
        f"Fator de conversão seco/úmido: **{br(FATORES_SECOS[material], 2)}** · "
        f"Volume seco: **{br(r['seco'], 3)} m³**."
    )
    st.markdown("#### Fórmulas do orçamento")
    st.latex(r"C_{materiais} = N_{sacos} P_{cimento} + V_{areia} P_{areia} + V_{brita} P_{brita}")
    st.latex(r"C_{total} = (C_{materiais} + C_{mao\ de\ obra} + C_{frete}) (1 + r/100)")
    st.caption("Para argamassa, o termo da brita é zero. A reserva financeira r é independente da perda física p.")
    st.warning(
        "**Premissas e limitações:** o traço é volumétrico e os fatores 1,54 (concreto) e 1,33 "
        "(argamassa) são aproximações empíricas. Foi adotada massa aparente do cimento de 1.440 kg/m³. "
        "Não há correção de umidade, inchamento da areia, granulometria, relação água/cimento ou controle "
        "tecnológico. Um traço nominal não assegura fck. Para concreto estrutural, use dosagem "
        "validada, projeto e responsabilidade técnica. Geometrias não retangulares devem ser tratadas à parte."
    )

st.markdown(
    '<div class="foot">'
    '<strong style="color:#b4f2e1">ObraQuant 3.1</strong> · '
    'Desenvolvido por <strong style="color:#e9f4ff">Wesley Goes Correa</strong><br>'
    'Quantitativos e custos preliminares · Engenharia com critérios transparentes'
    '</div>',
    unsafe_allow_html=True,
)
