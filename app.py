import os
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from streamlit_mic_recorder import speech_to_text
except Exception:
    speech_to_text = None


st.set_page_config(page_title="Assistente Ana Clara", page_icon="🎒", layout="centered")

# =====================================================
# CONFIGURAÇÃO GERAL
# =====================================================
APP_DIR = Path(__file__).resolve().parent
IMAGE_CANDIDATES = [APP_DIR, Path("/mnt/data")]

# A IA é opcional.
# O modo básico funciona sem API.
# Se quiser usar IA, configure OPENAI_API_KEY e altere USAR_IA para True.
OPENAI_MODEL = "gpt-4o-mini"
USAR_IA = True

# =====================================================
# VOZ NEURAL DA OPENAI
# =====================================================
# Se True, o app gera um áudio MP3 mais natural usando a API da OpenAI.
# Se a chave da API não estiver configurada, o app usa a voz simples do navegador como reserva.
USAR_TTS_OPENAI = True
TTS_MODEL = "gpt-4o-mini-tts"
TTS_VOICE = "coral"
TTS_INSTRUCTIONS = (
    "Fale em português do Brasil, com voz natural, carinhosa, clara e tranquila, "
    "como uma assistente escolar falando com uma criança. "
    "Use ritmo calmo, pronúncia brasileira e tom positivo."
)

# =====================================================
# HORÁRIO ESCOLAR
# =====================================================
HORARIO = {
    "segunda": ["Português", "Português", "Inglês", "Oficina de Leitura", "Escola da Inteligência"],
    "terca": ["História", "História", "Produção Textual", "Produção Textual", "Inglês"],
    "quarta": ["Ciências", "Ciências", "Matemática", "Matemática", "Inglês"],
    "quinta": ["Inglês", "Filosofia", "Português", "Português", "Arte", "Matemática"],
    "sexta": ["Educação Física", "Oficina de Leitura", "Inglês", "Geografia", "Geografia", "Matemática"],
}

HORARIOS_AULA = [
    "07:00 às 07:50",
    "07:50 às 08:40",
    "08:40 às 09:30",
    "09:50 às 10:40",
    "10:40 às 11:30",
    "11:30 às 12:20",
]

LIVRO_FILES = {
    "LIVRO_01_GERAL": "LIVRO 01 GERAL.jpg",
    "FICHA_ATIVIDADES": "FICHA_DE_ATIVIDADES.jpg",
    "INGLES": "Ingles.jpg",
    "ARTES": "LIVRO_ARTES.jpg",
    "FILOSOFIA": "LIVRO_FILOSOFIA.jpg",
}

DISCIPLINA_LIVRO = {
    "Português": ["LIVRO_02_GERAL", "FICHA_ATIVIDADES"],
    "Matemática": ["LIVRO_02_GERAL", "FICHA_ATIVIDADES"],
    "Ciências": ["LIVRO_02_GERAL", "FICHA_ATIVIDADES"],
    "História": ["LIVRO_02_GERAL", "FICHA_ATIVIDADES"],
    "Geografia": ["LIVRO_02_GERAL", "FICHA_ATIVIDADES"],
    "Produção Textual": ["LIVRO_02_GERAL", "FICHA_ATIVIDADES"],
    "Oficina de Leitura": ["LIVRO_02_GERAL", "FICHA_ATIVIDADES"],
    "Escola da Inteligência": ["LIVRO_02_GERAL", "FICHA_ATIVIDADES"],
    "Inglês": ["INGLES", "FICHA_ATIVIDADES"],
    "Filosofia": ["FILOSOFIA", "FICHA_ATIVIDADES"],
    "Arte": ["ARTES", "FICHA_ATIVIDADES"],
    "Educação Física": ["FICHA_ATIVIDADES"],
}

NOME_LIVRO = {
    "LIVRO_01_GERAL": "Livro 2 Geral",
    "FICHA_ATIVIDADES": "Ficha de Atividades",
    "INGLES": "Livro de Inglês",
    "ARTES": "Livro de Arte",
    "FILOSOFIA": "Livro de Filosofia",
}

DIA_LABELS = {
    "segunda": "Segunda-feira",
    "terca": "Terça-feira",
    "quarta": "Quarta-feira",
    "quinta": "Quinta-feira",
    "sexta": "Sexta-feira",
}

WEEKDAY_TO_DIA = {
    0: "segunda",
    1: "terca",
    2: "quarta",
    3: "quinta",
    4: "sexta",
}

# =====================================================
# CORPUS DE REFERÊNCIA DAS PROVAS
# =====================================================
# Este bloco funciona como um corpus interno de referência.
# Quando a criança pergunta sobre prova, data, disciplina, conteúdo ou estudo,
# a ferramenta consulta este corpus antes de responder sobre horário/livros.
#
# Vantagem: fica simples de atualizar. Quando chegar outro PDF da escola,
# você pode trocar ou ampliar apenas este bloco.
CORPUS_REFERENCIA_PROVAS = """
DOCUMENTO: Calendário de Provas - Turma 502 - 1º Trimestre

SEGUNDA-FEIRA - 18/05:
- Português
- Inglês

TERÇA-FEIRA - 19/05:
- História
- Produção Textual

QUARTA-FEIRA - 20/05:
- Matemática
- Ciências

QUINTA-FEIRA - 21/05:
- Filosofia
- Arte

SEXTA-FEIRA - 22/05:
- Educação Física
- Geografia

ORIENTAÇÕES DA SEMANA DE AVALIAÇÕES:
- Nos dias de PB, haverá aula normal.
- As avaliações serão aplicadas pelo professor da disciplina, durante o tempo de aula.
- Não haverá alteração nos horários de entrada e saída dos alunos.
- Não será permitida a utilização de aparelhos eletrônicos, como celulares, calculadoras e relógios smartwatch.
- Nos dias 25 e 26 de maio serão aplicadas as avaliações de segunda chamada.
- Caso o aluno deixe de realizar qualquer avaliação, deve justificar a ausência e preencher o requerimento de segunda chamada na secretaria da escola.


DOCUMENTO: Conteúdos Prova Semanal (PB) - 1º Trimestre - Turmas 501 e 502

DISCIPLINA: CIÊNCIAS
Livro 2:
- Resíduos que produzimos – p. 137.
- Classificando os resíduos – p. 139 a 143.
- Quanto lixo o Brasil produz e para onde vai? – p. 143 a 146.
- Coleta seletiva – p. 152.
- Origem dos materiais – p. 156 a 161.
- Propriedade dos materiais – p. 164 a 166.
- Magnetismo – p. 168.
- Densidade – p. 170.
- Solubilidade – p. 172.

DISCIPLINA: HISTÓRIA
Livro 2:
- Direito natural – p. 230.
- Declaração dos Direitos do Homem e do Cidadão – p. 231.
- ONU e a Declaração dos Direitos do Homem e do Cidadão/Organização das Nações Unidas (ONU)/Declaração Universal dos Direitos Humanos – p. 233.
- Refugiados e os direitos humanos – p. 235.
- Direitos humanos no Brasil/Direitos humanos e a ditadura civil-militar/Novo momento político – p. 237.
- Estatuto da Criança e do Adolescente – p. 239.
- Cidadania – p. 243.
- Diretas já – p. 244.
- Constituição brasileira de 1988 – p. 245.
- Luta das mulheres por direitos políticos – p. 249.
- Voto feminino no Brasil – p. 250.

DISCIPLINA: GEOGRAFIA
Livro 2:
- Tipos de cidades – p. 187 e 188.
- Agricultura e tipos de agricultura – p. 198 e 201.
- Agricultura Hidropônica – p. 202.
- Sistema intensivo e extensivo – p. 200 e 204.
- Pecuária – p. 203.
- Problemas Urbanos – p. 208 a 210.
- Problemas ambientais – p. 212 e 213.

DISCIPLINA: PRODUÇÃO TEXTUAL
Livro 2:
- Gênero texto de divulgação científica – p. 40 a 45 e p. 54 a 58.
- Informações gráficas – p. 59 a 63.
Livro paradidático 2:
- O aeroclube.

DISCIPLINA: LÍNGUA PORTUGUESA
Livro 2:
- Usos de -ICE e -ISSE – p. 46 a 49.
- Verbo principal e verbo auxiliar – p. 65 a 69.

DISCIPLINA: PORTUGUÊS
Livro 2:
- Usos de -ICE e -ISSE – p. 46 a 49.
- Verbo principal e verbo auxiliar – p. 65 a 69.

DISCIPLINA: MATEMÁTICA
Livro 2:
- Unidade 3 – capítulos 1 e 2 – p. 116 a 132.
- Estudar a tabuada do 6.

DISCIPLINA: FILOSOFIA
Livro 2:
- Dúvidas – p. 9 a 12.
- Sentimentos – p. 16, 18 e 20.
- René Descartes – p. 23, 24, 26, 27 e 28.

DISCIPLINA: INGLÊS
Units 2/3:
- All about health.
- Places of the city.
- Directions.
- Should – Shouldn’t.

DISCIPLINA: ARTE
Livro 2:
- Arquitetura – p. 9 a 11.
- Acústica – p. 17.
- Teatro improvisado – p. 24.
- Autos e folclore – p. 25 a 28.
- Dança de salão – p. 32.
- Danças Valsa, Maxixe, Salsa, Tango, Bolero e Chá-chá-chá – p. 34 a 37.

DISCIPLINA: EDUCAÇÃO FÍSICA
Livro 2:
- Brincadeiras nas aulas de Educação Física.
- Conhecendo novos jogos.
- Bolinha de gude, jogos rítmicos (adoleta), frisbee e jogos de tabuleiro.
"""

# Base estruturada derivada do corpus.
# A ferramenta usa isto para responder com mais precisão.
CALENDARIO_PROVAS = {
    "segunda": {"data": "18/05", "disciplinas": ["Português", "Inglês"]},
    "terca": {"data": "19/05", "disciplinas": ["História", "Produção Textual"]},
    "quarta": {"data": "20/05", "disciplinas": ["Matemática", "Ciências"]},
    "quinta": {"data": "21/05", "disciplinas": ["Filosofia", "Arte"]},
    "sexta": {"data": "22/05", "disciplinas": ["Educação Física", "Geografia"]},
}

CONTEUDOS_PROVAS = {
    "Ciências": [
        "Resíduos que produzimos – p. 137",
        "Classificando os resíduos – p. 139 a 143",
        "Quanto lixo o Brasil produz e para onde vai? – p. 143 a 146",
        "Coleta seletiva – p. 152",
        "Origem dos materiais – p. 156 a 161",
        "Propriedade dos materiais – p. 164 a 166",
        "Magnetismo – p. 168",
        "Densidade – p. 170",
        "Solubilidade – p. 172",
    ],
    "História": [
        "Direito natural – p. 230",
        "Declaração dos Direitos do Homem e do Cidadão – p. 231",
        "ONU, Organização das Nações Unidas e Declaração Universal dos Direitos Humanos – p. 233",
        "Refugiados e os direitos humanos – p. 235",
        "Direitos humanos no Brasil, ditadura civil-militar e novo momento político – p. 237",
        "Estatuto da Criança e do Adolescente – p. 239",
        "Cidadania – p. 243",
        "Diretas já – p. 244",
        "Constituição brasileira de 1988 – p. 245",
        "Luta das mulheres por direitos políticos – p. 249",
        "Voto feminino no Brasil – p. 250",
    ],
    "Geografia": [
        "Tipos de cidades – p. 187 e 188",
        "Agricultura e tipos de agricultura – p. 198 e 201",
        "Agricultura Hidropônica – p. 202",
        "Sistema intensivo e extensivo – p. 200 e 204",
        "Pecuária – p. 203",
        "Problemas Urbanos – p. 208 a 210",
        "Problemas ambientais – p. 212 e 213",
    ],
    "Produção Textual": [
        "Gênero texto de divulgação científica – p. 40 a 45 e p. 54 a 58",
        "Informações gráficas – p. 59 a 63",
        "Livro paradidático 2: O aeroclube",
    ],
    "Português": [
        "Usos de -ICE e -ISSE – p. 46 a 49",
        "Verbo principal e verbo auxiliar – p. 65 a 69",
    ],
    "Matemática": [
        "Unidade 3 – capítulos 1 e 2 – p. 116 a 132",
        "Estudar a tabuada do 6",
    ],
    "Filosofia": [
        "Dúvidas – p. 9 a 12",
        "Sentimentos – p. 16, 18 e 20",
        "René Descartes – p. 23, 24, 26, 27 e 28",
    ],
    "Inglês": [
        "Units 2/3",
        "All about health",
        "Places of the city",
        "Directions",
        "Should – Shouldn’t",
    ],
    "Arte": [
        "Arquitetura – p. 9 a 11",
        "Acústica – p. 17",
        "Teatro improvisado – p. 24",
        "Autos e folclore – p. 25 a 28",
        "Dança de salão – p. 32",
        "Danças Valsa, Maxixe, Salsa, Tango, Bolero e Chá-chá-chá – p. 34 a 37",
    ],
    "Educação Física": [
        "Brincadeiras nas aulas de Educação Física",
        "Conhecendo novos jogos",
        "Bolinha de gude, jogos rítmicos (adoleta), frisbee e jogos de tabuleiro",
    ],
}

SINONIMOS_DISCIPLINAS = {
    "Português": ["portugues", "português", "lingua portuguesa", "língua portuguesa"],
    "Inglês": ["ingles", "inglês", "english"],
    "História": ["historia", "história"],
    "Produção Textual": ["producao textual", "produção textual", "redacao", "redação"],
    "Matemática": ["matematica", "matemática", "mat"],
    "Ciências": ["ciencias", "ciências", "ciencia", "ciência"],
    "Filosofia": ["filosofia"],
    "Arte": ["arte", "artes"],
    "Educação Física": ["educacao fisica", "educação física", "ed fisica", "ed física"],
    "Geografia": ["geografia", "geo"],
}


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================
def remover_acentos(texto: str) -> str:
    texto = texto or ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def normalizar(texto: str) -> str:
    return remover_acentos(texto).strip().lower()


def dia_de_hoje_util(dia_padrao: str = "segunda") -> str:
    return WEEKDAY_TO_DIA.get(date.today().weekday(), dia_padrao)


def detectar_dia(texto: str, dia_padrao: str = "segunda") -> str:
    txt = normalizar(texto)

    if "segunda" in txt:
        return "segunda"
    if "terca" in txt:
        return "terca"
    if "quarta" in txt:
        return "quarta"
    if "quinta" in txt:
        return "quinta"
    if "sexta" in txt:
        return "sexta"
    if "hoje" in txt:
        return dia_de_hoje_util(dia_padrao)

    return dia_padrao


def get_api_key() -> str:
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        secret_key = ""
    env_key = os.getenv("OPENAI_API_KEY", "")
    return secret_key or env_key


@st.cache_resource
def get_openai_client() -> OpenAI | None:
    if OpenAI is None:
        return None
    api_key = get_api_key()
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def resolve_image_path(filename: str) -> Path | None:
    """Procura a imagem mesmo se o arquivo tiver variações como (1), espaços ou maiúsculas."""
    filename_path = Path(filename)
    possible_names = [
        filename,
        f"{filename_path.stem}(1){filename_path.suffix}",
        f"{filename_path.stem} (1){filename_path.suffix}",
    ]

    for base in IMAGE_CANDIDATES:
        for name in possible_names:
            candidate = base / name
            if candidate.exists():
                return candidate

        target = normalizar(filename_path.stem).replace(" ", "").replace("_", "")
        for candidate in base.glob("*"):
            if candidate.suffix.lower() not in [".jpg", ".jpeg", ".png", ".webp"]:
                continue
            candidate_key = normalizar(candidate.stem).replace(" ", "").replace("_", "").replace("(1)", "")
            if candidate_key == target:
                return candidate

    return None


def extrair_livros_do_dia(dia: str) -> list[str]:
    aulas = HORARIO.get(dia, [])
    livros: list[str] = []
    for disciplina in aulas:
        for livro in DISCIPLINA_LIVRO.get(disciplina, []):
            if livro not in livros:
                livros.append(livro)
    return livros


def horario_da_aula(indice: int) -> str:
    if indice < len(HORARIOS_AULA):
        return HORARIOS_AULA[indice]
    return f"{indice + 1}ª aula"


def listar_aulas_com_horario(dia: str) -> list[str]:
    aulas = HORARIO.get(dia, [])
    return [
        f"{horario_da_aula(i)} - {aula}"
        for i, aula in enumerate(aulas)
    ]


def formatar_aulas_com_horario(dia: str) -> str:
    itens = listar_aulas_com_horario(dia)
    return "; ".join(itens) if itens else "nenhuma aula cadastrada"


def montar_contexto_escolar(dia: str) -> str:
    aulas = HORARIO.get(dia, [])
    livros = extrair_livros_do_dia(dia)
    livros_legiveis = [NOME_LIVRO.get(codigo, codigo) for codigo in livros]

    return (
        f"Dia consultado: {DIA_LABELS.get(dia, dia)}.\n"
        f"Aulas do dia com horários: {formatar_aulas_com_horario(dia)}.\n"
        f"Livros do dia: {', '.join(livros_legiveis) if livros_legiveis else 'nenhum livro identificado'}.\n\n"
        f"Corpus de referência das provas:\n{CORPUS_REFERENCIA_PROVAS}"
    )


def montar_texto_para_fala(dia: str) -> str:
    aulas = HORARIO.get(dia, [])
    livros = extrair_livros_do_dia(dia)
    livros_legiveis = [NOME_LIVRO.get(codigo, codigo) for codigo in livros]
    dia_nome = DIA_LABELS.get(dia, dia)

    if not aulas:
        return f"Olá! Para {dia_nome}, não encontrei aulas cadastradas."

    aulas_texto = ", ".join(aulas)
    livros_texto = ", ".join(livros_legiveis)

    return (
        f"Olá! {dia_nome}, você tem aula de {aulas_texto}. "
        f"Não esqueça de levar: {livros_texto}. "
        "Organize sua mochila com calma, confira todo o material e deixe tudo pronto. "
        "Tenha uma ótima aula!"
    )



def limitar_texto_para_audio(texto: str, limite: int = 1800) -> str:
    """
    Evita enviar textos muito longos para o TTS.
    Para respostas grandes, corta com segurança e mantém a voz objetiva.
    """
    texto = (texto or "").strip()
    if len(texto) <= limite:
        return texto
    return texto[:limite].rsplit(" ", 1)[0] + ". A resposta completa está escrita na tela."


def gerar_audio_openai(texto: str) -> bytes | None:
    """
    Gera voz neural com a API da OpenAI.
    Retorna bytes MP3 ou None se não conseguir gerar.
    """
    if not USAR_TTS_OPENAI:
        return None

    if OpenAI is None:
        return None

    api_key = get_api_key()
    if not api_key:
        return None

    texto_audio = limitar_texto_para_audio(texto)

    if not texto_audio:
        return None

    try:
        client = OpenAI(api_key=api_key)

        # Modelo gpt-4o-mini-tts aceita instruções de estilo.
        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=texto_audio,
            instructions=TTS_INSTRUCTIONS,
            response_format="mp3",
        )

        return response.content

    except TypeError:
        # Reserva para versões antigas da biblioteca openai que não aceitam "instructions".
        try:
            client = OpenAI(api_key=api_key)
            response = client.audio.speech.create(
                model=TTS_MODEL,
                voice=TTS_VOICE,
                input=texto_audio,
                response_format="mp3",
            )
            return response.content
        except Exception as e:
            st.warning(f"Não consegui gerar a voz neural agora. Usei a voz simples como reserva. Detalhe técnico: {e}")
            return None

    except Exception as e:
        st.warning(f"Não consegui gerar a voz neural agora. Usei a voz simples como reserva. Detalhe técnico: {e}")
        return None


def mostrar_audio_resposta(texto: str):
    """
    Mostra o áudio da resposta.
    Prioridade:
    1. Voz neural da OpenAI.
    2. Voz simples do navegador como reserva.
    """
    texto = (texto or "").strip()

    if not texto:
        st.info("Não há texto para falar.")
        return

    if USAR_TTS_OPENAI and get_api_key():
        chave_audio = f"{hash(texto)}_{TTS_MODEL}_{TTS_VOICE}"

        if st.session_state.get("ultimo_audio_chave") != chave_audio:
            with st.spinner("Gerando voz neural..."):
                st.session_state.ultimo_audio_bytes = gerar_audio_openai(texto)
                st.session_state.ultimo_audio_chave = chave_audio

        audio_bytes = st.session_state.get("ultimo_audio_bytes")

        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
            return

    if USAR_TTS_OPENAI and not get_api_key():
        st.warning("A voz neural está ligada, mas a OPENAI_API_KEY não foi encontrada. Usando a voz simples do navegador.")

    mostrar_botao_falar(texto)


def mostrar_botao_falar(texto: str):
    """Cria um botão no navegador para ler a resposta em voz alta."""
    texto_json = json.dumps(texto, ensure_ascii=False)
    components.html(
        f"""
        <div style=\"margin-top: 8px; margin-bottom: 12px;\">
            <button onclick=\"falarResposta()\"
                style=\"
                    width: 100%;
                    min-height: 52px;
                    border-radius: 12px;
                    border: none;
                    background: #ffb703;
                    color: #111;
                    font-size: 20px;
                    font-weight: 700;
                    cursor: pointer;
                \">
                🔊 Ouvir resposta em voz alta
            </button>
        </div>

        <script>
        const textoResposta = {texto_json};

        function falarResposta() {{
            if (!('speechSynthesis' in window)) {{
                alert('Este navegador não tem suporte para leitura em voz. Tente usar Chrome ou Edge.');
                return;
            }}

            window.speechSynthesis.cancel();

            const fala = new SpeechSynthesisUtterance(textoResposta);
            fala.lang = 'pt-BR';
            fala.rate = 0.92;
            fala.pitch = 1.05;
            fala.volume = 1;

            const vozes = window.speechSynthesis.getVoices();
            const vozBR = vozes.find(v => v.lang && v.lang.toLowerCase().startsWith('pt-br'));
            if (vozBR) {{
                fala.voice = vozBR;
            }}

            window.speechSynthesis.speak(fala);
        }}
        </script>
        """,
        height=90,
    )


# =====================================================
# FUNÇÕES DO CORPUS DE PROVAS
# =====================================================
def detectar_disciplina(pergunta: str) -> str | None:
    pergunta_norm = normalizar(pergunta)

    for disciplina, sinonimos in SINONIMOS_DISCIPLINAS.items():
        for termo in sinonimos:
            if termo in pergunta_norm:
                return disciplina

    return None


def detectar_data(pergunta: str) -> str | None:
    """
    Detecta datas escritas como:
    - 18/05
    - 18-05
    - dia 18
    - no dia 18
    - 18

    Como o calendário atual é de maio, quando a pessoa fala apenas "18",
    a ferramenta interpreta como 18/05.
    """
    pergunta_norm = normalizar(pergunta)

    # Formato completo: 18/05 ou 18-05
    match = re.search(r"\b(\d{1,2})[\/\-](\d{1,2})\b", pergunta_norm)
    if match:
        dia = match.group(1).zfill(2)
        mes = match.group(2).zfill(2)
        return f"{dia}/{mes}"

    # Formato: dia 18 / no dia 18
    match = re.search(r"\bdia\s+(\d{1,2})\b", pergunta_norm)
    if match:
        dia = match.group(1).zfill(2)
        return f"{dia}/05"

    # Formato simples: "18", "19", "20", "21", "22", "25", "26"
    # Só assume maio se o número aparecer sozinho na pergunta.
    match = re.search(r"\b(18|19|20|21|22|25|26)\b", pergunta_norm)
    if match:
        dia = match.group(1).zfill(2)
        return f"{dia}/05"

    return None



def detectar_datas(pergunta: str) -> list[str]:
    """
    Detecta uma ou mais datas na mesma pergunta.

    Exemplos reconhecidos:
    - "Tem prova dia 21 e 22?"
    - "Tem prova nos dias 21 e 22?"
    - "Quais provas em 21/05 e 22/05?"
    - "Provas de 18 a 22?"
    """
    pergunta_norm = normalizar(pergunta)
    datas: list[str] = []

    # Datas completas: 21/05, 22-05
    for dia, mes in re.findall(r"\b(\d{1,2})[\/\-](\d{1,2})\b", pergunta_norm):
        data = f"{dia.zfill(2)}/{mes.zfill(2)}"
        if data not in datas:
            datas.append(data)

    # Intervalos simples: 18 a 22
    intervalo = re.search(r"\b(18|19|20|21|22|25|26)\s+a\s+(18|19|20|21|22|25|26)\b", pergunta_norm)
    if intervalo:
        inicio = int(intervalo.group(1))
        fim = int(intervalo.group(2))
        if inicio <= fim:
            for d in range(inicio, fim + 1):
                data = f"{str(d).zfill(2)}/05"
                if data not in datas:
                    datas.append(data)

    # Números soltos do calendário atual: 18, 19, 20, 21, 22, 25, 26
    for dia in re.findall(r"\b(18|19|20|21|22|25|26)\b", pergunta_norm):
        data = f"{dia.zfill(2)}/05"
        if data not in datas:
            datas.append(data)

    return datas


def disciplinas_por_data(data: str) -> list[str]:
    for info in CALENDARIO_PROVAS.values():
        if info["data"] == data:
            return info["disciplinas"]
    return []


def data_da_disciplina(disciplina: str) -> tuple[str | None, str | None]:
    for dia, info in CALENDARIO_PROVAS.items():
        if disciplina in info["disciplinas"]:
            return info["data"], dia
    return None, None


def pergunta_sobre_prova(pergunta: str) -> bool:
    p = normalizar(pergunta)
    termos = [
        "prova", "avaliacao", "avaliação", "pb", "teste",
        "conteudo", "conteúdo", "cair", "estudar",
        "segunda chamada", "2 chamada", "2ª chamada",
        "calendario", "calendário"
    ]
    return any(normalizar(t) in p for t in termos)


def buscar_trechos_no_corpus(pergunta: str, limite: int = 6) -> list[str]:
    """
    Busca simples por palavras-chave no corpus.
    Esta função simula uma recuperação de contexto: separa o corpus em linhas e retorna
    as linhas mais compatíveis com a pergunta.
    """
    pergunta_norm = normalizar(pergunta)
    palavras = [
        p for p in re.findall(r"\w+", pergunta_norm)
        if len(p) >= 4 and p not in ["prova", "sobre", "quero", "saber", "quando", "qual", "quais", "conteudo", "conteudos"]
    ]

    linhas = [linha.strip() for linha in CORPUS_REFERENCIA_PROVAS.splitlines() if linha.strip()]
    pontuadas = []

    for linha in linhas:
        linha_norm = normalizar(linha)
        pontos = sum(1 for palavra in palavras if palavra in linha_norm)

        if re.search(r"\d{2}/\d{2}", linha_norm):
            pontos += 1
        if "disciplina" in linha_norm:
            pontos += 1

        if pontos > 0:
            pontuadas.append((pontos, linha))

    pontuadas.sort(key=lambda x: x[0], reverse=True)
    return [linha for _, linha in pontuadas[:limite]]


def responder_prova_modo_basico(pergunta: str) -> str | None:
    """
    Responde perguntas sobre provas usando o corpus estruturado.
    Retorna None quando a pergunta não parece ser sobre prova.
    """
    if not pergunta_sobre_prova(pergunta):
        return None

    pergunta_norm = normalizar(pergunta)
    disciplina = detectar_disciplina(pergunta)
    datas_perguntadas = detectar_datas(pergunta)
    data_perguntada = datas_perguntadas[0] if datas_perguntadas else detectar_data(pergunta)
    dia_perguntado = detectar_dia(pergunta, dia_padrao="")

    if "segunda chamada" in pergunta_norm or "2 chamada" in pergunta_norm or "2ª chamada" in pergunta_norm:
        return (
            "As avaliações de segunda chamada serão aplicadas nos dias 25 e 26 de maio. "
            "Caso o aluno deixe de realizar alguma avaliação, é necessário justificar a ausência "
            "e preencher o requerimento de segunda chamada na secretaria da escola."
        )

    if any(t in pergunta_norm for t in ["celular", "calculadora", "smartwatch", "relogio", "relógio", "aparelho eletronico", "aparelho eletrônico"]):
        return (
            "Durante as avaliações, não será permitida a utilização de aparelhos eletrônicos, "
            "como celulares, calculadoras e relógios smartwatch."
        )

    if any(t in pergunta_norm for t in ["entrada", "saida", "saída", "horario normal", "aula normal"]):
        return (
            "Nos dias de PB, haverá aula normal. As avaliações serão aplicadas pelo professor "
            "da disciplina, durante o tempo de aula. Não haverá alteração nos horários de entrada e saída."
        )

    if disciplina and any(t in pergunta_norm for t in ["cair", "conteudo", "conteúdo", "estudar", "materia", "matéria"]):
        conteudos = CONTEUDOS_PROVAS.get(disciplina, [])
        data_prova, dia_prova = data_da_disciplina(disciplina)
        if conteudos:
            lista = "\n".join([f"- {item}" for item in conteudos])
            inicio = f"Para a prova de {disciplina}"
            if data_prova:
                inicio += f", marcada para {DIA_LABELS.get(dia_prova, dia_prova)} ({data_prova})"
            return f"{inicio}, estude:\n{lista}"

    if disciplina and any(t in pergunta_norm for t in ["quando", "data", "dia", "calendario", "calendário", "prova"]):
        data_prova, dia_prova = data_da_disciplina(disciplina)
        if data_prova:
            return f"A prova de {disciplina} será na {DIA_LABELS.get(dia_prova, dia_prova)}, dia {data_prova}."

    # Pergunta com uma ou várias datas, por exemplo:
    # "Tem prova dia 21 e 22?"
    # "Quais provas tem nos dias 18, 19 e 20?"
    if datas_perguntadas:
        respostas_datas = []
        for data in datas_perguntadas:
            materias = disciplinas_por_data(data)
            if materias:
                respostas_datas.append(
                    f"No dia {data}, as provas serão de: {', '.join(materias)}."
                )
            else:
                respostas_datas.append(
                    f"No dia {data}, não encontrei prova cadastrada no calendário."
                )

        if respostas_datas:
            return "\n".join(respostas_datas)

    if data_perguntada:
        materias = disciplinas_por_data(data_perguntada)
        if materias:
            return f"No dia {data_perguntada}, as provas serão de: {', '.join(materias)}."

    if dia_perguntado in CALENDARIO_PROVAS:
        info = CALENDARIO_PROVAS[dia_perguntado]
        return (
            f"Na {DIA_LABELS.get(dia_perguntado, dia_perguntado)}, dia {info['data']}, "
            f"as provas serão de: {', '.join(info['disciplinas'])}."
        )

    if any(t in pergunta_norm for t in ["calendario", "calendário", "datas", "semana de prova", "semana de provas"]):
        linhas = []
        for dia, info in CALENDARIO_PROVAS.items():
            linhas.append(
                f"- {DIA_LABELS.get(dia, dia)} ({info['data']}): {', '.join(info['disciplinas'])}"
            )
        return "Calendário de provas da Turma 502:\n" + "\n".join(linhas)

    if any(t in pergunta_norm for t in ["conteudo", "conteúdo", "cair", "estudar"]):
        return (
            "Eu consigo dizer o conteúdo por disciplina. "
            "Pergunte, por exemplo: 'O que vai cair na prova de Matemática?' "
            "ou 'O que estudar para Ciências?'."
        )

    trechos = buscar_trechos_no_corpus(pergunta)
    if trechos:
        return "Encontrei estas informações no corpus de referência:\n" + "\n".join([f"- {t}" for t in trechos])

    return (
        "Não encontrei essa informação no corpus de referência das provas. "
        "Tente perguntar pela disciplina, pela data ou pelo dia da semana."
    )


def responder_prova_com_ia(pergunta: str) -> str | None:
    """
    Usa IA para responder perguntas sobre prova, com base exclusiva no corpus.

    Importante:
    - Antes de chamar a IA, a ferramenta tenta responder pelo modo estruturado.
    - Isso evita erro em perguntas objetivas, como: "Dia 18 tem prova?"
    - A IA fica para deixar a resposta mais flexível, mas não substitui a base oficial.
    """
    if not pergunta_sobre_prova(pergunta):
        return None

    # Primeiro tenta a resposta determinística/estruturada.
    # Para datas e disciplinas, isso é mais seguro do que depender só da IA.
    resposta_basica = responder_prova_modo_basico(pergunta)
    if resposta_basica and not resposta_basica.startswith("Não encontrei"):
        return resposta_basica

    client = get_openai_client()
    if client is None:
        return resposta_basica

    calendario_estruturado = []
    for dia, info in CALENDARIO_PROVAS.items():
        calendario_estruturado.append(
            f"{DIA_LABELS.get(dia, dia)} - {info['data']}: {', '.join(info['disciplinas'])}"
        )

    conteudos_estruturados = []
    for disciplina, conteudos in CONTEUDOS_PROVAS.items():
        conteudos_estruturados.append(
            f"{disciplina}: " + "; ".join(conteudos)
        )

    contexto_completo = (
        "CALENDÁRIO ESTRUTURADO DAS PROVAS:\n"
        + "\n".join(calendario_estruturado)
        + "\n\nCONTEÚDOS ESTRUTURADOS DAS PROVAS:\n"
        + "\n".join(conteudos_estruturados)
        + "\n\nCORPUS ORIGINAL DE REFERÊNCIA:\n"
        + CORPUS_REFERENCIA_PROVAS
    )

    system_prompt = (
        "Você é o Assistente Escolar Ana Clara. "
        "Responda em português do Brasil, de forma simples, curta, amigável e objetiva. "
        "Use somente o calendário, os conteúdos e o corpus de referência fornecidos. "
        "Não invente datas, conteúdos, disciplinas ou regras. "
        "Quando a pergunta citar uma data, informe as disciplinas daquele dia. "
        "Quando a pergunta citar uma disciplina, informe a data e, se perguntarem, o conteúdo. "
        "Se a informação não estiver no corpus, diga que não encontrou a informação."
    )

    user_prompt = (
        f"Base oficial de referência:\n{contexto_completo}\n\n"
        f"Pergunta da criança ou responsável:\n{pergunta}"
    )

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        return response.output_text.strip()
    except Exception as e:
        st.warning(f"A IA não respondeu agora. Usei o modo básico. Detalhe técnico: {e}")
        return resposta_basica or responder_prova_modo_basico(pergunta)


# =====================================================
# RESPOSTAS SOBRE AULAS E LIVROS
# =====================================================
def responder_modo_basico(pergunta: str, dia: str) -> str:
    pergunta_lower = normalizar(pergunta)
    aulas = HORARIO.get(dia, [])
    livros = extrair_livros_do_dia(dia)
    livros_legiveis = [NOME_LIVRO.get(codigo, codigo) for codigo in livros]

    if not aulas:
        return f"Não encontrei aulas cadastradas para {DIA_LABELS.get(dia, dia)}."

    if "ingles" in pergunta_lower:
        return "Sim, tem Inglês nesse dia." if "Inglês" in aulas else "Não, não tem Inglês nesse dia."

    if "filosofia" in pergunta_lower:
        return "Sim, tem Filosofia nesse dia." if "Filosofia" in aulas else "Não, não tem Filosofia nesse dia."

    if "arte" in pergunta_lower:
        return "Sim, tem Arte nesse dia." if "Arte" in aulas else "Não, não tem Arte nesse dia."

    aulas_com_horario = formatar_aulas_com_horario(dia)

    if "livro" in pergunta_lower or "material" in pergunta_lower or "levar" in pergunta_lower:
        return (
            f"Para {DIA_LABELS.get(dia, dia)}, leve: {', '.join(livros_legiveis)}. "
            f"As aulas são: {aulas_com_horario}."
        )

    if "aula" in pergunta_lower or "materia" in pergunta_lower or "matéria" in pergunta_lower or "horario" in pergunta_lower or "horário" in pergunta_lower:
        return f"As aulas de {DIA_LABELS.get(dia, dia)} são: {aulas_com_horario}."

    return (
        f"Em {DIA_LABELS.get(dia, dia)}, as aulas são: {aulas_com_horario}. "
        f"Os livros para levar são: {', '.join(livros_legiveis)}."
    )


def responder_com_ia(pergunta: str, dia: str) -> str:
    client = get_openai_client()
    if client is None:
        return responder_modo_basico(pergunta, dia)

    contexto = montar_contexto_escolar(dia)
    system_prompt = (
        "Você é o Assistente Escolar Ana Clara. "
        "Responda em português do Brasil, com linguagem simples, amigável, curta e objetiva. "
        "Use somente as informações do contexto escolar fornecido. "
        "Se a pergunta for sobre livros ou materiais, diga exatamente quais levar. "
        "A Ficha de Atividades deve ser considerada material de todos os dias. "
        "Se a pergunta for sobre provas, use o corpus de referência das provas. "
        "Não invente horários, tarefas, datas, conteúdos ou disciplinas."
    )
    user_prompt = f"Contexto escolar:\n{contexto}\n\nPergunta:\n{pergunta}"

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        return response.output_text.strip()
    except Exception as e:
        st.warning(f"A IA não respondeu agora. Usei o modo básico. Detalhe técnico: {e}")
        return responder_modo_basico(pergunta, dia)


def responder_pergunta(pergunta: str, dia: str) -> str:
    """
    Ordem de resposta:
    1. Se a pergunta for sobre prova, consulta o corpus de referência.
    2. Caso contrário, responde sobre aulas, horários e livros.
    """
    if USAR_IA:
        resposta_prova = responder_prova_com_ia(pergunta)
    else:
        resposta_prova = responder_prova_modo_basico(pergunta)

    if resposta_prova:
        return resposta_prova

    if USAR_IA:
        return responder_com_ia(pergunta, dia)
    return responder_modo_basico(pergunta, dia)


def registrar_resposta(pergunta: str):
    pergunta = (pergunta or "").strip()
    if not pergunta:
        st.warning("Digite uma pergunta ou use um dos botões rápidos.")
        return

    dia_da_pergunta = detectar_dia(pergunta, dia_padrao=st.session_state.dia_selecionado)
    st.session_state.dia_selecionado = dia_da_pergunta
    st.session_state.ultimo_dia_consultado = dia_da_pergunta

    with st.spinner("Pensando..."):
        resposta = responder_pergunta(pergunta, dia_da_pergunta)
        texto_fala = resposta

    st.session_state.ultimo_texto_fala = texto_fala
    st.session_state.chat.append(("Você", pergunta))
    st.session_state.chat.append(("Assistente", resposta))


def mostrar_livros(livros: list[str]):
    if not livros:
        st.info("Nenhum livro identificado para esse dia.")
        return

    cols = st.columns(min(len(livros), 3))
    for idx, livro in enumerate(livros):
        col = cols[idx % len(cols)]
        with col:
            st.markdown(f"**{NOME_LIVRO.get(livro, livro)}**")
            image_path = resolve_image_path(LIVRO_FILES[livro])
            if image_path:
                st.image(str(image_path), use_container_width=True)
            else:
                st.warning(f"Imagem não encontrada: {LIVRO_FILES[livro]}")


def mostrar_calendario_provas():
    st.subheader("📝 Calendário de provas")
    for dia, info in CALENDARIO_PROVAS.items():
        st.write(f"**{DIA_LABELS.get(dia, dia)} ({info['data']}):** {', '.join(info['disciplinas'])}")


def mostrar_conteudos_provas():
    st.subheader("📖 Conteúdos das provas")
    for disciplina, conteudos in CONTEUDOS_PROVAS.items():
        with st.expander(f"{disciplina}"):
            for item in conteudos:
                st.write(f"- {item}")


# =====================================================
# ESTADO
# =====================================================
if "chat" not in st.session_state:
    st.session_state.chat = []

if "dia_selecionado" not in st.session_state:
    st.session_state.dia_selecionado = dia_de_hoje_util("segunda")

if "ultimo_dia_consultado" not in st.session_state:
    st.session_state.ultimo_dia_consultado = st.session_state.dia_selecionado

if "texto_pergunta" not in st.session_state:
    st.session_state.texto_pergunta = ""

if "ultimo_texto_voz" not in st.session_state:
    st.session_state.ultimo_texto_voz = ""

if "ultimo_texto_fala" not in st.session_state:
    st.session_state.ultimo_texto_fala = ""

if "ultimo_audio_bytes" not in st.session_state:
    st.session_state.ultimo_audio_bytes = None

if "ultimo_audio_chave" not in st.session_state:
    st.session_state.ultimo_audio_chave = ""


# =====================================================
# CABEÇALHO
# =====================================================
st.title("🎒 Assistente Escolar Ana Clara")
st.caption("Digite a pergunta. Eu respondo sobre aulas, horários, livros, datas de provas e conteúdos das provas.")

if USAR_IA and not get_api_key():
    st.warning("A IA está ligada, mas a OPENAI_API_KEY não foi encontrada. Configure a chave da API para a IA funcionar.")
elif USAR_IA and get_api_key():
    st.success("IA ativada: a ferramenta está usando a API da OpenAI para responder com mais flexibilidade.")

st.markdown(
    """
    <style>
    div[data-testid="stTextArea"] textarea {
        font-size: 22px !important;
        min-height: 120px !important;
        border-radius: 14px !important;
    }
    div.stButton > button {
        font-size: 16px !important;
        min-height: 48px !important;
        border-radius: 12px !important;
    }
    div[data-testid="stFormSubmitButton"] button {
        font-size: 20px !important;
        min-height: 52px !important;
        border-radius: 12px !important;
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# PERGUNTA
# =====================================================
st.markdown("### 💬 O que você quer saber hoje?")

st.markdown("#### 🎙️ Opção de voz")
st.caption("Clique no microfone, fale a pergunta e aguarde o texto aparecer no campo abaixo. Depois clique em Responder ✅.")

if speech_to_text is None:
    st.info(
        "Para ativar a voz, instale a biblioteca streamlit-mic-recorder. "
        "No terminal, use: pip install streamlit-mic-recorder"
    )
else:
    texto_voz = speech_to_text(
        language="pt-BR",
        start_prompt="🎙️ Falar pergunta",
        stop_prompt="⏹️ Parar gravação",
        just_once=True,
        use_container_width=True,
        key="gravador_voz",
    )

    if texto_voz and texto_voz != st.session_state.ultimo_texto_voz:
        st.session_state.ultimo_texto_voz = texto_voz
        st.session_state.texto_pergunta = texto_voz.strip()
        st.success(f"Texto gerado pela voz: {texto_voz}")


with st.form("form_pergunta", clear_on_submit=False):
    texto_digitado = st.text_area(
        "Digite sua pergunta ou use a voz acima",
        placeholder=(
            "Ex.: Que aulas tenho hoje? Quais livros preciso levar? "
            "Quando é a prova de Matemática? O que vai cair em Ciências?"
        ),
        height=120,
        key="texto_pergunta",
    )
    enviar = st.form_submit_button("Responder ✅", type="primary")

if enviar:
    registrar_resposta(texto_digitado)


st.write("Ou clique em uma pergunta pronta:")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📚 Que livros levar?", key="btn_livros"):
        registrar_resposta("Que livros preciso levar hoje?")
with col2:
    if st.button("⏰ Quais aulas tenho?", key="btn_aulas"):
        registrar_resposta("Quais aulas eu tenho hoje?")
with col3:
    if st.button("📝 Provas da semana", key="btn_provas"):
        registrar_resposta("Qual é o calendário de provas da semana?")

col4, col5, col6 = st.columns(3)
with col4:
    if st.button("➗ Prova de Matemática", key="btn_matematica"):
        registrar_resposta("Quando é a prova de Matemática e o que vai cair?")
with col5:
    if st.button("🔬 Prova de Ciências", key="btn_ciencias"):
        registrar_resposta("Quando é a prova de Ciências e o que vai cair?")
with col6:
    if st.button("🇬🇧 Tenho inglês hoje?", key="btn_ingles"):
        registrar_resposta("Tenho inglês hoje?")


with st.expander("⚙️ Escolher dia padrão, caso a pergunta diga apenas 'hoje'", expanded=False):
    dias = list(HORARIO.keys())
    dia = st.selectbox(
        "Dia padrão",
        options=dias,
        index=dias.index(st.session_state.dia_selecionado),
        format_func=lambda x: DIA_LABELS.get(x, x.title()),
        key="select_dia",
    )
    st.session_state.dia_selecionado = dia


# =====================================================
# RESULTADO
# =====================================================
if not st.session_state.chat:
    st.info("Estou esperando a pergunta. Depois eu mostro a resposta e, se for útil, as aulas e os livros.")

if st.session_state.chat:
    dia_resposta = st.session_state.ultimo_dia_consultado
    aulas_resposta = HORARIO.get(dia_resposta, [])
    livros_resposta = extrair_livros_do_dia(dia_resposta)

    st.subheader("✅ Resposta")

    ultima_resposta = None
    for autor, mensagem in reversed(st.session_state.chat):
        if autor == "Assistente":
            ultima_resposta = mensagem
            break

    if ultima_resposta:
        st.success(ultima_resposta)

    texto_fala_atual = st.session_state.ultimo_texto_fala or ultima_resposta or montar_texto_para_fala(dia_resposta)
    st.subheader("🔊 Resposta falada")
    st.info(texto_fala_atual)
    mostrar_audio_resposta(texto_fala_atual)

    with st.expander(f"📚 Ver aulas de {DIA_LABELS.get(dia_resposta, dia_resposta)}", expanded=False):
        if aulas_resposta:
            for i, aula in enumerate(aulas_resposta, start=1):
                st.write(f"{i}. {horario_da_aula(i - 1)} - {aula}")
        else:
            st.info("Não há aulas cadastradas para esse dia.")

    with st.expander("🧾 Ver livros para levar", expanded=False):
        mostrar_livros(livros_resposta)

    with st.expander("🗂️ Ver conversa completa", expanded=False):
        for autor, mensagem in st.session_state.chat:
            if autor == "Você":
                st.markdown(f"**{autor}:** {mensagem}")
            else:
                st.success(mensagem)


# =====================================================
# CONSULTA VISUAL AO CORPUS
# =====================================================
with st.expander("📝 Ver calendário de provas", expanded=False):
    mostrar_calendario_provas()

with st.expander("📖 Ver conteúdos das provas", expanded=False):
    mostrar_conteudos_provas()

with st.expander("📚 Ver corpus de referência das provas", expanded=False):
    st.text(CORPUS_REFERENCIA_PROVAS)


# =====================================================
# DIAGNÓSTICO DAS IMAGENS
# =====================================================
with st.expander("🤖 Diagnóstico da IA e da voz", expanded=False):
    st.write(f"USAR_IA: {USAR_IA}")
    st.write(f"Modelo de texto configurado: {OPENAI_MODEL}")
    st.write(f"USAR_TTS_OPENAI: {USAR_TTS_OPENAI}")
    st.write(f"Modelo de voz configurado: {TTS_MODEL}")
    st.write(f"Voz configurada: {TTS_VOICE}")
    if get_api_key():
        st.success("OPENAI_API_KEY encontrada. A IA e a voz neural podem ser usadas.")
    else:
        st.warning("OPENAI_API_KEY não encontrada. O app vai cair no modo básico e usará a voz simples do navegador.")
    if OpenAI is None:
        st.error("Biblioteca openai não foi importada. Instale com: python -m pip install openai")


with st.expander("🔧 Diagnóstico das imagens"):
    for codigo, arquivo in LIVRO_FILES.items():
        caminho = resolve_image_path(arquivo)
        if caminho:
            st.success(f"{NOME_LIVRO[codigo]}: encontrado em {caminho.name}")
        else:
            st.error(f"{NOME_LIVRO[codigo]}: não encontrado. Esperado: {arquivo}")


with st.expander("🔧 Como configurar a API no Streamlit Cloud"):
    st.markdown(
        """
A API da OpenAI é opcional neste aplicativo. O modo básico funciona sem IA.

Se quiser usar IA:

1. Abra o app no Streamlit Cloud.
2. Vá em **Settings → Secrets**.
3. Adicione:

```toml
OPENAI_API_KEY = "sua_chave_aqui"
```

4. Neste arquivo, o código já está com `USAR_IA = True`.
5. Salve e reinicie o app.

Observação:
- Mesmo sem IA, o aplicativo consulta o corpus de referência das provas.
- Com IA ativada, o aplicativo usa o corpus como contexto e responde de forma mais flexível.
- Com a voz neural ativada, o app também usa a API da OpenAI para gerar um áudio MP3 mais natural da resposta.
        """
    )
