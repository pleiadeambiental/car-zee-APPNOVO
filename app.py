import streamlit as st
import pandas as pd
import geopandas as gpd
import base64
from pathlib import Path
import time

st.set_page_config(page_title="Consulta CAR x ZEE", layout="wide")

# ⶜ Logo da empresa
logo_path = Path("logo_empresa.png")
col1, col2 = st.columns([1, 4])

with col1:
    if logo_path.exists():
        img_base64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{img_base64}" style="width:120px; margin-top:10px;">',
            unsafe_allow_html=True
        )
    else:
        st.warning("Logo não encontrada.")

with col2:
    st.markdown("### Descubra em que zona do ZEE-TO seu imóvel está")

st.markdown(
    "#### Informe o número do CAR e receba um resumo técnico com percentuais, restrições e oportunidades"
)
st.markdown("---")

# ⶜ Funções cacheadas
@st.cache_data(show_spinner=False)
def carregar_shapefile(path):
    return gpd.read_file(path)

@st.cache_data(show_spinner=False)
def preparar_com_crs(path, epsg=5880):
    gdf = gpd.read_file(path)
    if not gdf.crs.is_projected or gdf.crs.to_epsg() != epsg:
        gdf = gdf.to_crs(epsg=epsg)
    return gdf

# ⶜ Dicionário de descrições (resumido aqui por brevidade)
descricoes_zonas = {
     "Zonas Especiais de Unidades de Conservação de Proteção Integral": {
        "titulo": "Zonas Especiais de Unidades de Conservação de Proteção Integral (ZEPIs)",
        "categoria": "Restritiva",
        "descricao": (
            "As ZEPIs abrangem todas as unidades de conservação de proteção integral, em conformidade com o Sistema Nacional de Unidades de Conservação (SNUC), tendo como objetivo básico “preservar a natureza, sendo admitido apenas o uso indireto dos seus recursos naturais” (BRASIL, 2000, Artigo 7º, Parágrafo 1º). Esse tipo de utilização é entendido como “aquele que não envolve consumo, coleta, dano ou destruição dos recursos naturais” (BRASIL, 2000, Artigo 2º, Inciso IX)."
        )
    },
    "Zonas Especiais de Unidades de Conservação de Uso Sustentável": {
        "titulo": "Zonas Especiais de Unidades de Conservação de Uso Sustentável (ZEUSs)",
        "categoria": "Restritiva",
        "descricao": (
            "As ZEUS abrangem todas as unidades de conservação de uso sustentável e têm o objetivo básico de “compatibilizar a conservação da natureza com o uso sustentável de parcela dos seus recursos naturais” (BRASIL, 2000, Artigo 7º, Parágrafo 2º). Esse tipo de utilização é entendido como a “exploração do ambiente de maneira a garantir a perenidade dos recursos ambientais renováveis e dos processos ecológicos, mantendo a biodiversidade e os demais atributos ecológicos, de forma socialmente justa e economicamente viável” (BRASIL, 2000, Artigo 2º, Inciso XI)."
        )
    },
    "Zonas Especiais de Terras Indígenas": {
        "titulo": "Zonas Especiais de Terras Indígenas (ZETIs)",
        "categoria": "Restritiva",
        "descricao": (
            "As ZETIs compreendem terras ocupadas ou habitadas pelos povos indígenas (bens inalienáveis da União), cabendo-lhes a posse permanente “e o direito ao usufruto exclusivo das riquezas naturais e de todas as utilidades”, incluindo o “uso dos mananciais e das águas dos trechos das vias fluviais” entendidos, como o produto da sua exploração econômica” (BRASIL, 1973, Artigos 22-24)."
        )
    },
    "Zonas de Desenvolvimento Integrado 1": {
        "titulo": "Zonas de Desenvolvimento Integrado 1 (ZDIs-1)",
        "categoria": "Restritiva",
        "descricao": (
            "As ZDIs-1 têm como objetivo básico garantir a proteção e a restauração muito intensiva dos ecossistemas naturais em harmonia com as dinâmicas sociais e econômicas. Apresentam **vocação máxima para a conservação ecológica e implantação de serviços ambientais e potencial mínimo para dinamização do desenvolvimento socioeconômico**, consideradas as limitações e capacidades de suporte do meio natural. Compreendem áreas com predominância de fragilidade biológica e/ou suscetibilidade física muito alta e alta."
        )
    },
    "Zonas de Desenvolvimento Integrado 2": {
        "titulo": "Zonas de Desenvolvimento Integrado 2 (ZDIs-2)",
        "categoria": "Restritiva",
        "descricao": (
            "As ZDIs-2 têm como objetivo básico garantir a proteção e a restauração intensiva dos ecossistemas naturais em harmonia com as dinâmicas sociais e econômicas. Apresentam **vocação muito alta para a conservação ecológica e implantação de serviços ambientais e potencial muito baixo para dinamização do desenvolvimento socioeconômico**, consideradas as limitações e capacidades de suporte do meio natural. Compreendem áreas com predominância de fragilidade biológica e/ou suscetibilidade física muito alta e alta."
        )
    },
    "Zonas de Desenvolvimento Integrado 3": {
        "titulo": "Zonas de Desenvolvimento Integrado 3 (ZDI-3)",
        "categoria": "Intermediária",
        "descricao": (
            "As ZDIs-3 têm como objetivo básico garantir a proteção e a restauração dos ecossistemas naturais em harmonia com as dinâmicas sociais e econômicas. Apresentam **vocação alta para a conservação ecológica e implantação de serviços ambientais e potencial baixo para dinamização do desenvolvimento socioeconômico**, consideradas as limitações e capacidades de suporte do meio natural. Compreendem áreas com predominância de fragilidade biológica e/ou suscetibilidade física alta."
        )
    },
    "Zonas de Desenvolvimento Integrado 4": {
        "titulo": "Zonas de Desenvolvimento Integrado 4 (ZDI-4)",
        "categoria": "Intermediária",
        "descricao": (
            "As ZDIs-4 têm como objetivo básico garantir a proteção e a restauração dos ecossistemas naturais em equilíbrio com a dinamização do desenvolvimento socioeconômico. Apresentam **vocação média superior para a conservação ecológica e implantação de serviços ambientais e potencial médio inferior para dinamização do desenvolvimento socioeconômico**, consideradas as limitações e capacidades de suporte do meio natural. Compreendem áreas com predominância de fragilidade biológica e/ou suscetibilidade física alta."
        )
    },
    "Zonas de Consolidação Estratégica 4": {
        "titulo": "Zonas de Consolidação Estratégica 4 (ZCEs-4)",
        "categoria": "Intermediária",
        "descricao": (
            "As ZCE-4 têm como objetivo básico promover usos diretos da terra para fins produtivos em equilíbrio com a capacidade de suporte do meio natural, e a conservação e recuperação de remanescentes naturais. Apresentam **potencial médio superior para dinamização do desenvolvimento socioeconômico considerando o uso sustentável dos recursos naturais e vocação média inferior para a conservação ecológica**. Compreendem áreas com vulnerabilidade natural variando entre baixa a alta."
        )
    },
    "Zonas de Consolidação Estratégica 3": {
        "titulo": "Zonas de Consolidação Estratégica 3 (ZCEs-3)",
        "categoria": "Produtiva",
        "descricao": (
            "As ZCE-3 têm como objetivo básico promover a dinamização socioeconômica em equilíbrio com a capacidade de suporte do meio natural e os limites legais de proteção ambiental. Apresentam **potencial alto para dinamização do desenvolvimento socioeconômico considerando o uso sustentável dos recursos naturais e vocação baixa para a conservação ecológica**. Compreendem áreas com vulnerabilidade natural variando entre baixa a alta."
        )
    },
    "Zonas de Consolidação Estratégica 2": {
        "titulo": "Zonas de Consolidação Estratégica 2 (ZCEs-2)",
        "categoria": "Produtiva",
        "descricao": (
            "As ZCE-2 têm como objetivo básico promover a dinamização socioeconômica intensa em equilíbrio com a capacidade de suporte do meio natural e os limites legais de proteção ambiental. Apresentam **potencial muito alto para dinamização do desenvolvimento socioeconômico considerando o uso sustentável dos recursos naturais e vocação muito baixa para a conservação ecológica**. Compreendem áreas com predominância de vulnerabilidade natural baixa."
        )
    },
    "Zonas de Consolidação Estratégica 1": {
        "titulo": "Zonas de Consolidação Estratégica 1 (ZCEs-1)",
        "categoria": "Produtiva",
        "descricao": (
            "As ZCE-1 têm como objetivo básico promover a dinamização socioeconômica muito intensa em equilíbrio com a capacidade de suporte do meio natural e os limites legais de proteção ambiental. Apresentam **potencial máximo para dinamização do desenvolvimento socioeconômico considerando o uso sustentável dos recursos naturais e vocação mínima para a conservação ecológica**. Compreendem áreas com predominância de vulnerabilidade natural baixa e muito baixa."
        )
    }
}

# ⶜ Função principal
def analisar_intersecao(numero_car: str, path_car: str, path_zee: str, path_apse: str):
    gdf_car = carregar_shapefile(path_car)
    gdf_zee = preparar_com_crs(path_zee)
    gdf_ecos = preparar_com_crs(path_apse)

    imovel = gdf_car[gdf_car['numero_car'] == numero_car]
    if imovel.empty:
        return {"erro": "Número do CAR não encontrado"}

    nome_imovel = imovel.iloc[0]['nom_imovel']
    imovel = imovel.to_crs(gdf_zee.crs)

    # Filtro espacial para performance
    bbox = imovel.total_bounds
    gdf_zee = gdf_zee.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    gdf_ecos = gdf_ecos.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]

    intersecao = gpd.overlay(imovel, gdf_zee, how='intersection')
    intersecao['area_ha'] = intersecao.geometry.area / 10_000
    area_total = imovel.geometry.area.iloc[0] / 10_000
    intersecao['percentual'] = (intersecao['area_ha'] / area_total) * 100

    zonas_resultado = [
        {"zona": row["zona"], "percentual": f"{row['percentual']:.2f}".replace('.', ',')}
        for _, row in intersecao.iterrows()
    ]

    zonas_presentes = sorted(set(row["zona"] for row in zonas_resultado))

    intersecao_ecos = gpd.overlay(imovel, gdf_ecos, how='intersection')
    apses = []
    if not intersecao_ecos.empty and 'serv_ecos' in intersecao_ecos.columns:
        intersecao_ecos['area_ha'] = intersecao_ecos.geometry.area / 10_000
        intersecao_ecos['percentual'] = intersecao_ecos['area_ha'] / area_total * 100
        apses = [
            {"servico": row['serv_ecos'], "percentual": f"{row['percentual']:.2f}".replace('.', ',')}
            for _, row in intersecao_ecos.iterrows()
        ]

    return {
        "numero_car": numero_car,
        "nome_imovel": nome_imovel,
        "zonas": zonas_resultado,
        "zonas_presentes": zonas_presentes,
        "descricoes_zonas": {
            z: descricoes_zonas.get(z, {"titulo": z, "categoria": "—", "descricao": "_sem descrição_"})
            for z in zonas_presentes
        },
        "apses": apses
    }

# ⶜ Formulário
numero_car = st.text_input("Número do CAR")

if st.button("Consultar"):
    if not numero_car:
        st.warning("Por favor, digite o número do CAR.")
        st.stop()

    with st.spinner("Cruzando dados geoespaciais. Quase pronto!"):
        time.sleep(0.5)
        resultado = analisar_intersecao(
            numero_car,
            "app/data/car.shp",
            "app/data/zee.shp",
            "app/data/servicos_ecossistemicos_4674.shp"
        )

    if "erro" in resultado:
        st.error(resultado["erro"])
        st.stop()

    st.success(f"Imóvel: {resultado['nome_imovel']}  \nCAR: {resultado['numero_car']}")

    if resultado["zonas"]:
        df = pd.DataFrame(resultado["zonas"])
        df["%"] = df["percentual"].str.replace(",", ".").astype(float)
        df["%"] = df["%"].map(lambda x: f"{x:.2f}".replace('.', ','))
        df = df.rename(columns={"zona": "Zona"})[["Zona", "%"]]
        st.markdown("### Zoneamento Ecológico-Econômico (ZEE)")
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption("Dados oficiais do Zoneamento Ecológico-Econômico do Tocantins – versão 2025. Projeto de Lei encaminhado à ALETO em 02 abr 2025.")

    st.markdown("### O que significa para você?")
    for zona in resultado["zonas_presentes"]:
        info = resultado["descricoes_zonas"][zona]
        st.markdown(f"**{info['titulo']}**")
        st.markdown(f"**Categoria:** {info['categoria']}")
        st.markdown(info["descricao"])
        st.markdown("---")

    st.markdown("### Áreas Prioritárias para Serviços Ecossistêmicos (APSE)")
    apses = resultado.get("apses", [])
    if apses:
        df_apse = pd.DataFrame(apses)
        df_apse["%"] = df_apse["percentual"].str.replace(",", ".").astype(float)
        df_apse["%"] = df_apse["%"].map(lambda x: f"{x:.2f}".replace('.', ','))
        df_apse = df_apse.rename(columns={"servico": "Serviço"})[["Serviço", "%"]]
        st.dataframe(df_apse, use_container_width=True, hide_index=True)

        st.markdown("### O que significa para você?")
        st.markdown("""
As **Áreas Prioritárias para Serviços Ecossistêmicos (APSE)** são porções territoriais propostas no ZEE-TO com o objetivo principal de **conservar os recursos hídricos**, proteger remanescentes de vegetação nativa e **potencializar usos sustentáveis do território**, especialmente aqueles baseados em subprodutos do meio natural. Essas áreas atuam de forma **suplementar ao zoneamento** principal, sendo definidas a partir de fundamentos estruturantes e tendências de crescimento do estado.
 
As APSE correspondem a **áreas com funções ecológicas estratégicas**, como **Reservas Legais, vegetação nativa, fundos de vale e mananciais**, incluindo espaços com baixa aptidão produtiva, mas alta relevância ambiental. Como consta nas diretrizes do ZEE, uma das metas centrais é **“conservar áreas de florestas e outros ambientes naturais nas Áreas Prioritárias para Serviços Ecossistêmicos, mais notadamente os habitats que contenham alta diversidade de flora e fauna.”** Essas áreas também integram ações de **educação ambiental, PSA, REDD+ e compensações legais**, sendo peças-chave na transição para modelos produtivos sustentáveis no Tocantins.
        """)

        st.caption("Dados oficiais do Zoneamento Ecológico-Econômico do Tocantins – versão 2025. Projeto de Lei encaminhado à ALETO em 02 abr 2025.")
    else:
        st.info("O imóvel objeto de análise não intersecta nenhuma Área Prioritária para Serviços Ecossistêmicos (APSE).")

    st.markdown("---")
    st.markdown("#### Fale com a Plêiade", unsafe_allow_html=True)
    st.markdown('''
    <a href="https://wa.me/5563981017774" target="_blank">
        <button style="background-color:#25D366;color:white;border:none;
        padding:10px 20px;font-size:16px;border-radius:5px;cursor:pointer;">
            📞 WhatsApp
        </button>
    </a>
    ''', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("Aviso legal: “Este resultado é orientativo e não substitui análise técnica nem licenciamento ambiental. Consulte um profissional habilitado.”")
    st.caption("Atualizado em 05/06/2025")
