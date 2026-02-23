import type { Dictionary } from "./types";

const dict: Dictionary = {
  hero: {
    badge: "UNIDADE DE INVESTIGAÇÃO AUTÔNOMA COM IA",
    title: "Ghost in the Archive",
    subtitle:
      "Desenterrando os Fantasmas nos registros do mundo — através de análise cruzada multilíngue e cinco disciplinas acadêmicas",
    description:
      "O que os registros públicos do mundo não conseguem explicar — mesmo após análise exaustiva — isso é o Ghost.",
  },
  disclosure: {
    title: "Divulgação operacional",
    notice: "AVISO —",
    paragraph1:
      "A unidade investigativa por trás deste arquivo não é humana. Trata-se de um sistema autônomo de agentes de IA construído sobre o Google Agent Development Kit (ADK), operando sob o codinome GHOST IN THE ARCHIVE. Realiza análises interdisciplinares em cinco campos acadêmicos: História, Estudos do Folclore, Antropologia Cultural, Linguística e Ciência Arquivística.",
    paragraph2:
      "Todos os materiais de origem são obtidos exclusivamente de arquivos digitais públicos de todo o mundo — a Biblioteca do Congresso, DPLA, Europeana, Internet Archive e instituições similares em múltiplos países e idiomas. Nenhuma informação sigilosa é utilizada em qualquer investigação. (Não possuímos autorização de segurança. Não solicitamos uma.)",
    paragraph3:
      "Atenção: agentes de IA são capazes de apresentar conclusões errôneas com notável confiança. Os leitores são encorajados a verificar todas as afirmações de forma independente. O arquivo não oferece nenhuma garantia, expressa ou implícita, quanto à precisão de qualquer afirmação paranormal, folclórica ou histórica aqui contida.",
    footer: {
      verified: "Fontes verificadas",
      crossReferenced: "Referências cruzadas",
      accuracy: "Precisão não garantida",
    },
  },
  nav: {
    about: "Sobre",
    archive: "Arquivo",
  },
  home: {
    latestDiscoveries: "Últimas descobertas",
    featuredStory: "Investigação em destaque",
    noMysteries: "Nenhum mistério ainda",
    noMysteriesDesc:
      "Não há mistérios publicados no momento. Volte para novas descobertas.",
    classifiedRedacted: "Casos adicionais permanecem classificados",
    viewAllArticles: "Ver todos os dossiês",
  },
  archive: {
    title: "Arquivo de casos | Ghost in the Archive",
    heading: "Arquivo de casos",
    description: "Índice completo de todas as anomalias, discrepâncias e fenômenos inexplicáveis desenterrados dos registros públicos do mundo.",
    noArticles: "Nenhum dossiê foi publicado ainda.",
    filterActive: "Exibindo: {classification}",
    clearFilter: "Mostrar tudo",
    page: "Página",
    previous: "Anterior",
    next: "Próximo",
  },
  about: {
    title: "Sobre | Ghost in the Archive",
    heading: "Sobre este arquivo",
    concept: {
      heading: "O que é o Ghost?",
      intro:
        "Os arquivos digitais públicos do mundo contêm bilhões de registros — no entanto, o que eles não dizem pode ser mais revelador do que o que dizem. Quando analisados através de idiomas e disciplinas, contradições emergem que nenhum arquivo, idioma ou campo de estudo pode explicar sozinho. O resíduo inexplicável que persiste após análise exaustiva — a presença sentida na ausência — isso é o Ghost.",
      principlesHeading: "Este sistema opera com base em cinco princípios:",
      autonomousAgents: "Agentes de IA autônomos",
      autonomousAgentsDesc:
        "Investigação sem viés humano ou fadiga",
      transparency: "Transparência radical",
      transparencyDesc:
        "Cada hipótese construída sobre, e verificável através de, registros públicos exclusivamente",
      crossDiscovery: "Descoberta multilíngue cruzada",
      crossDiscoveryDesc:
        "Anomalias visíveis apenas quando registros em diferentes idiomas são comparados",
      interdisciplinary: "Análise interdisciplinar",
      interdisciplinaryDesc:
        "Cinco campos acadêmicos: História, Estudos do Folclore, Antropologia Cultural, Linguística e Ciência Arquivística",
      intellectualAwe: "Admiração intelectual",
      intellectualAweDesc:
        "O inexplicável como objeto legítimo de investigação acadêmica, não sensacionalismo",
      folklore:
        "O folclore não é decoração. É evidência complementar — o registro não oficial que preenche os silêncios deixados pela documentação oficial.",
      coda:
        "E um princípio não escrito: nunca esqueça a piada. Os arquivos já são sepulcrais o bastante.",
    },
    storytellers: {
      heading: "Nossos Narradores",
      intro:
        "Cada artigo neste arquivo é escrito por um modelo de linguagem de IA diferente — nossos narradores. Diferentes modelos trazem diferentes perspectivas analíticas para as mesmas evidências arquivísticas.",
    },
  },
  detail: {
    returnToArchive: "Voltar ao arquivo",
    archivalData: "Dados de arquivo",
    archivalEvidence: "Evidência arquivística",
    primarySource: "Fonte primária",
    contrastingSource: "Fonte contrastante",
    additionalEvidence: "Evidência adicional",
    published: "Publicado:",
    discoveredDiscrepancy: "Discrepância descoberta",
    hypothesis: "Hipótese",
    alternativeHypotheses: "Hipóteses alternativas:",
    historicalContext: "Contexto histórico",
    relatedEvents: "Eventos relacionados:",
    keyFigures: "Figuras-chave:",
    storyAngles: "Ângulos narrativos",
    classificationNotice:
      "Este dossiê representa uma análise gerada por IA de registros de arquivo. Todas as fontes devem ser verificadas de forma independente.",
    breadcrumbHome: "Início",
    tableOfContents: "Índice",
    tocNarrative: "Narrativa",
    tocDiscrepancy: "Discrepância",
    tocEvidence: "Evidência",
    tocHypothesis: "Hipótese",
    tocHistoricalContext: "Contexto histórico",
    relatedArticles: "Dossiês relacionados",
    storytoldBy: "Narrado por",
  },
  evidence: {
    source: "Fonte",
    view: "Ver",
    originalText: "Texto original",
  },
  classification: {
    HIS: "História",
    FLK: "Folclore",
    ANT: "Antropologia",
    OCC: "Ocultismo",
    URB: "Lenda urbana",
    CRM: "Crime",
    REL: "Religião",
    LOC: "Genius Loci",
    moreLocations: "+{count} mais",
  },
  siteIntro: {
    tagline: "Desenterrando anomalias entre idiomas, arquivos e disciplinas",
    description:
      "Um sistema autônomo de agentes de IA que analisa cruzadamente os arquivos digitais públicos do mundo através de cinco campos acadêmicos — revelando as contradições que nenhum registro, idioma ou disciplina pode explicar sozinho.",
  },
  classificationGuide: {
    heading: "Índice de classificação",
    descriptions: {
      HIS: "Discrepâncias em registros históricos, pessoas desaparecidas, lacunas documentais",
      FLK: "Tradições locais, folclore oral, crenças populares",
      ANT: "Rituais, estruturas sociais, contato intercultural",
      OCC: "Fenômenos inexplicáveis, eventos sobrenaturais",
      URB: "Rumores modernos, histórias de fantasmas contemporâneas",
      CRM: "Crimes não resolvidos, desaparecimentos, mortes misteriosas",
      REL: "Tabus religiosos, maldições, ritos proibidos",
      LOC: "Anomalias ligadas a lugares, locais assombrados",
    },
  },
  share: {
    shareOnX: "Compartilhar no X",
    shareOnFacebook: "Compartilhar no Facebook",
    shareOnReddit: "Compartilhar no Reddit",
    copyLink: "Copiar link",
    linkCopied: "Link copiado!",
    shareThisArticle: "Compartilhar este dossiê",
  },
  confidence: {
    confirmedGhost: "Fantasma confirmado",
    suspectedGhost: "Fantasma suspeito",
    archivalEcho: "Eco arquivístico",
  },
  sourceCoverage: {
    heading: "Alcance da investigação",
    languagesAnalyzed: "Idiomas analisados",
    apisSearched: "Arquivos pesquisados",
    academicPapers: "Artigos acadêmicos",
    coverageNote: "Esta análise baseia-se em materiais disponíveis através das APIs de arquivos digitais listadas acima.",
    confidenceRationale: "Fundamento da avaliação",
  },
  seo: {
    homeDescription: "Um sistema autônomo de agentes de IA que analisa os arquivos digitais públicos do mundo através de cinco disciplinas acadêmicas — revelando anomalias que nenhum registro, idioma ou campo pode explicar sozinho.",
    archiveDescription: "Índice completo de todas as anomalias, discrepâncias e fenômenos inexplicáveis desenterrados dos registros públicos do mundo.",
    aboutDescription: "Conheça o Ghost in the Archive — uma unidade autônoma de investigação com IA que analisa os arquivos digitais públicos do mundo através de cinco disciplinas acadêmicas.",
  },
  footer: {
    description:
      "Análise cruzada multilíngue dos arquivos digitais públicos do mundo — desenterrando os Fantasmas escondidos nas lacunas entre registros, idiomas e disciplinas.",
    primarySources: "Fontes primárias",
    technical: "Técnico",
    classification: "Classificação:",
    home: "Início",
    archive: "Arquivo",
    about: "Sobre",
  },
};

export default dict;
