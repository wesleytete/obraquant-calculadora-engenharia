# 🏗️ ObraQuant — Calculadora de Insumos e Pré-Orçamento de Obras

**Autor: Wesley Goes Correa**  

Aplicativo web interativo desenvolvido em **Python + Streamlit** para apoiar estimativas preliminares de consumo de cimento, areia e brita em serviços de concreto e argamassa.

> **Projeto de portfólio — Engenharia Civil e desenvolvimento de software.** A ferramenta é educacional e de pré-orçamento. Não substitui projeto estrutural, dosagem experimental de concreto nem orçamento executivo.

## Funcionalidades

- Seleção de material e elemento construtivo (laje, pilar, sapata, baldrame, contrapiso e revestimentos, conforme o tipo de material).
- Entrada de dimensões em metros ou centímetros, repetição de elementos e taxa de perdas.
- Estimativa de materiais a partir de traços **volumétricos** configurados.
- Quantitativos de cimento em sacos de 50 kg, areia e brita em m³.
- Orçamento preliminar com preços editáveis, frete, mão de obra e reserva financeira.
- Dashboard analítico com gráfico de rosca dos volumes aparentes de insumos e comparação de perdas de 5%, 10% e 15%.
- Resumos, memória das premissas e exportação CSV.

## Tecnologias

- Python
- Streamlit — interface web
- Plotly — gráficos interativos

## Rodar localmente

Instale Python e, no terminal aberto na pasta do projeto, execute:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app_calculadora_insumos.py
```

Abra o endereço informado pelo terminal (normalmente `http://localhost:8501`).

## Publicar no Streamlit Community Cloud

1. Crie um repositório público no GitHub e envie os arquivos deste diretório (não apenas o ZIP).
2. Acesse https://share.streamlit.io/ e selecione **Create app**.
3. Escolha o repositório e a branch `main`.
4. No campo do arquivo principal (*entrypoint*), informe `app_calculadora_insumos.py`.
5. Selecione **Deploy** e teste a URL pública fornecida.

## Exemplo demonstrativo

Laje maciça de 4,00 m × 5,00 m × 0,12 m, 1 unidade, traço 1:2:3 e 10% de perdas:

- Volume geométrico: **2,400 m³**
- Volume planejado: **2,640 m³**
- Cimento: **20 sacos de 50 kg**
- Areia: **1,355 m³** (aproximadamente)
- Brita: **2,033 m³** (aproximadamente)

Os resultados são calculados a partir dos **fatores empíricos** definidos no código. Valores de preço são exemplos editáveis e não cotações de mercado.

## Limitações de engenharia

- Os traços representam proporções volumétricas; **não garantem fck** nem desempenho mecânico.
- O fator de conversão para materiais secos, a massa específica aparente do cimento e a reserva de perdas são aproximações que podem não corresponder às condições reais da obra.
- Ajustes podem ser necessários para aberturas, variações de espessura, formas geométricas especiais e umidade dos agregados.
- O orçamento é preliminar e não substitui uma composição completa de custos, especificações e verificações do responsável técnico.

## Links do projeto

- **Aplicativo online:** adicione aqui a URL após publicar no Streamlit Cloud.
- **Código-fonte:** adicione aqui a URL do repositório no GitHub.

## Estado

Versão de portfólio **3.1**, desenvolvida por **Wesley Goes Correa**, preparada para publicação. Teste a versão implantada antes de divulgar o link.
