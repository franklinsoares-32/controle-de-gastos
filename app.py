import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pandas as pd
import json

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Controle de Gastos",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS personalizado ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
}

.stApp {
    background: #0f0f13;
    color: #f0ede8;
}

/* Cards de métricas */
[data-testid="metric-container"] {
    background: #1a1a22;
    border: 1px solid #2a2a38;
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
}

[data-testid="metric-container"] label {
    color: #888 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f0ede8 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* Inputs */
.stTextInput input, .stNumberInput input, .stSelectbox select {
    background: #1a1a22 !important;
    border: 1px solid #2a2a38 !important;
    border-radius: 10px !important;
    color: #f0ede8 !important;
}

/* Botão principal */
.stButton > button {
    background: #c8f535 !important;
    color: #0f0f13 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 2rem !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.03em;
}

.stButton > button:hover {
    background: #d9ff4d !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(200, 245, 53, 0.3) !important;
}

/* Tabela */
[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid #2a2a38;
}

/* Divisor */
hr {
    border-color: #2a2a38 !important;
}

/* Select box */
[data-baseweb="select"] {
    background: #1a1a22 !important;
}

[data-baseweb="select"] * {
    background: #1a1a22 !important;
    color: #f0ede8 !important;
}

.header-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    color: #f0ede8;
    margin-bottom: 0;
}

.header-sub {
    color: #555;
    font-size: 0.9rem;
    margin-top: 0.2rem;
    margin-bottom: 2rem;
}

.accent {
    color: #c8f535;
}

.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #c8f535;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 1rem;
    margin-top: 1.5rem;
}

.badge {
    display: inline-block;
    background: #1a1a22;
    border: 1px solid #2a2a38;
    border-radius: 999px;
    padding: 0.2rem 0.8rem;
    font-size: 0.75rem;
    color: #888;
    margin-right: 0.4rem;
}

.success-box {
    background: rgba(200, 245, 53, 0.08);
    border: 1px solid rgba(200, 245, 53, 0.3);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    color: #c8f535;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ── Conexão com Google Sheets ────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def conectar_sheets():
    """Conecta ao Google Sheets usando as credenciais do secrets."""
    try:
        import os
import json

creds_dict = json.loads(os.environ["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        return None

def abrir_planilha(client, nome_planilha: str):
    """Abre a planilha pelo nome. Cria o cabeçalho se estiver vazia."""
    try:
        sheet = client.open(nome_planilha).sheet1
        # Verifica se tem cabeçalho
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "Data":
            sheet.insert_row(["Data", "Descrição", "Categoria", "Valor (R$)"], 1)
        return sheet
    except gspread.SpreadsheetNotFound:
        st.error(f'Planilha "{nome_planilha}" não encontrada. Verifique o nome e se foi compartilhada com a service account.')
        return None

def carregar_gastos(sheet) -> pd.DataFrame:
    """Carrega todos os gastos da planilha como DataFrame."""
    try:
        dados = sheet.get_all_records()
        if not dados:
            return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Valor (R$)"])
        df = pd.DataFrame(dados)
        df["Valor (R$)"] = pd.to_numeric(df["Valor (R$)"], errors="coerce").fillna(0)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def adicionar_gasto(sheet, data: str, descricao: str, categoria: str, valor: float):
    """Adiciona uma nova linha na planilha."""
    sheet.append_row([data, descricao, categoria, valor])

def deletar_gasto(sheet, indice_linha: int):
    """Deleta uma linha da planilha (índice começa em 2, pois linha 1 é o cabeçalho)."""
    sheet.delete_rows(indice_linha + 2)  # +2: cabeçalho + índice 0-based

# ── Categorias disponíveis ───────────────────────────────────────────────────
CATEGORIAS = [
    "🍔 Alimentação",
    "🚗 Transporte",
    "🏠 Moradia",
    "💊 Saúde",
    "🎓 Educação",
    "🎮 Lazer",
    "👗 Vestuário",
    "💡 Contas / Utilidades",
    "📱 Tecnologia",
    "🐾 Pet",
    "🎁 Presentes",
    "📦 Outros",
]

# ── Interface principal ──────────────────────────────────────────────────────
st.markdown('<p class="header-title">💸 Controle de <span class="accent">Gastos</span></p>', unsafe_allow_html=True)
st.markdown(f'<p class="header-sub">Registre e acompanhe seus gastos mensais — {datetime.now().strftime("%B de %Y")}</p>', unsafe_allow_html=True)

# Nome da planilha (configurável via secrets ou input)
nome_planilha = st.secrets.get("SHEET_NAME", "Controle de Gastos")

client = conectar_sheets()
if not client:
    st.stop()

sheet = abrir_planilha(client, nome_planilha)
if not sheet:
    st.stop()

df = carregar_gastos(sheet)

# ── Métricas do mês atual ────────────────────────────────────────────────────
st.markdown('<p class="section-title">📊 Resumo do Mês</p>', unsafe_allow_html=True)

mes_atual = datetime.now().strftime("%m/%Y")

if not df.empty and "Data" in df.columns:
    df_mes = df[df["Data"].astype(str).str.endswith(mes_atual)]
else:
    df_mes = pd.DataFrame()

col1, col2, col3 = st.columns(3)

total_mes = df_mes["Valor (R$)"].sum() if not df_mes.empty else 0
total_geral = df["Valor (R$)"].sum() if not df.empty else 0
qtd_lancamentos = len(df_mes) if not df_mes.empty else 0

col1.metric("Total do Mês", f"R$ {total_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("Lançamentos no Mês", qtd_lancamentos)
col3.metric("Total Geral", f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# ── Formulário de novo gasto ─────────────────────────────────────────────────
col_form, col_tabela = st.columns([1, 1.6], gap="large")

with col_form:
    st.markdown('<p class="section-title">➕ Novo Gasto</p>', unsafe_allow_html=True)

    with st.form("form_gasto", clear_on_submit=True):
        data_gasto = st.date_input("📅 Data", value=date.today())
        descricao = st.text_input("📝 Descrição", placeholder="Ex: Mercado, Uber, Aluguel...")
        categoria = st.selectbox("🏷️ Categoria", CATEGORIAS)
        valor = st.number_input("💰 Valor (R$)", min_value=0.01, step=0.01, format="%.2f")

        submitted = st.form_submit_button("Registrar Gasto", use_container_width=True)

        if submitted:
            if not descricao.strip():
                st.warning("Por favor, preencha a descrição.")
            else:
                data_str = data_gasto.strftime("%d/%m/%Y")
                adicionar_gasto(sheet, data_str, descricao.strip(), categoria, round(valor, 2))
                st.markdown('<div class="success-box">✅ Gasto registrado com sucesso!</div>', unsafe_allow_html=True)
                st.cache_resource.clear()
                st.rerun()

# ── Tabela de gastos ─────────────────────────────────────────────────────────
with col_tabela:
    st.markdown('<p class="section-title">📋 Lançamentos</p>', unsafe_allow_html=True)

    filtro = st.selectbox(
        "Filtrar por",
        ["Mês atual", "Todos os lançamentos"],
        label_visibility="collapsed"
    )

    df_exibir = df_mes if filtro == "Mês atual" else df

    if df_exibir.empty:
        st.info("Nenhum gasto registrado ainda.")
    else:
        # Exibe tabela formatada
        st.dataframe(
            df_exibir,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Valor (R$)": st.column_config.NumberColumn(
                    "Valor (R$)",
                    format="R$ %.2f",
                )
            }
        )

        # Gráfico de gastos por categoria
        if not df_exibir.empty:
            st.markdown('<p class="section-title">📈 Por Categoria</p>', unsafe_allow_html=True)
            resumo = df_exibir.groupby("Categoria")["Valor (R$)"].sum().sort_values(ascending=False)
            st.bar_chart(resumo)

# ── Deletar lançamento ───────────────────────────────────────────────────────
if not df.empty:
    st.markdown("---")
    st.markdown('<p class="section-title">🗑️ Remover Lançamento</p>', unsafe_allow_html=True)

    opcoes = [
        f"{i+1}. {row['Data']} | {row['Descrição']} | {row['Categoria']} | R$ {row['Valor (R$)']:.2f}"
        for i, row in df.iterrows()
    ]

    col_del1, col_del2 = st.columns([3, 1])
    with col_del1:
        selecionado = st.selectbox("Selecione o lançamento para remover:", opcoes, label_visibility="collapsed")
    with col_del2:
        if st.button("🗑️ Remover", use_container_width=True):
            idx = opcoes.index(selecionado)
            deletar_gasto(sheet, idx)
            st.success("Lançamento removido!")
            st.cache_resource.clear()
            st.rerun()
