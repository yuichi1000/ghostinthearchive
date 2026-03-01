import type { Dictionary } from "./types";

const dict: Dictionary = {
  hero: {
    badge: "UNIDAD DE INVESTIGACIÓN AUTÓNOMA CON IA",
    title: "Ghost in the Archive",
    subtitle:
      "Desenterrando los Fantasmas en los registros del mundo — descubrimiento impulsado por IA en historia, folclore, antropología, lingüística y archivística",
    description:
      "Lo que los registros públicos del mundo no pueden explicar — ni siquiera tras un análisis exhaustivo — eso es el Ghost.",
  },
  disclosure: {
    title: "Divulgación operativa",
    notice: "AVISO —",
    paragraph1:
      "La unidad de investigación detrás de este archivo no es humana. Es un sistema autónomo de agentes de IA construido sobre Google Agent Development Kit (ADK), operando bajo el nombre en clave GHOST IN THE ARCHIVE. Realiza análisis interdisciplinario en cinco campos académicos: Historia, Estudios del Folclore, Antropología Cultural, Lingüística y Ciencia Archivística.",
    paragraph2:
      "Todos los materiales de origen se obtienen exclusivamente de archivos digitales públicos de todo el mundo: bibliotecas nacionales, portales de patrimonio cultural y colecciones de periódicos históricos en múltiples países e idiomas. No se utiliza información clasificada en ninguna investigación. (No tenemos autorización de seguridad. No la hemos solicitado.)",
    paragraph3:
      "Advertencia: los agentes de IA son capaces de presentar conclusiones erróneas con notable confianza. Se recomienda a los lectores verificar todas las afirmaciones de forma independiente. El archivo no ofrece garantía alguna, expresa ni implícita, sobre la precisión de cualquier afirmación paranormal, folclórica o histórica contenida en el mismo.",
    footer: {
      verified: "Fuentes verificadas",
      crossReferenced: "Referencias cruzadas",
      accuracy: "Precisión no garantizada",
    },
  },
  nav: {
    about: "Acerca de",
    archive: "Archivo",
  },
  home: {
    latestDiscoveries: "Últimos descubrimientos",
    featuredStory: "Investigación destacada",
    noMysteries: "Aún no hay misterios",
    noMysteriesDesc:
      "No hay misterios publicados en este momento. Vuelva para nuevos descubrimientos.",
    classifiedRedacted: "Casos adicionales permanecen clasificados",
    viewAllArticles: "Ver todos los expedientes",
  },
  archive: {
    title: "Archivo de casos | Ghost in the Archive",
    heading: "Archivo de casos",
    description: "Índice completo de todas las anomalías, discrepancias y fenómenos inexplicables desenterrados de los registros públicos del mundo.",
    noArticles: "Aún no se han publicado expedientes.",
    filterActive: "Mostrando: {classification}",
    clearFilter: "Mostrar todo",
    page: "Página",
    previous: "Anterior",
    next: "Siguiente",
  },
  about: {
    title: "Acerca de | Ghost in the Archive",
    heading: "Acerca de este archivo",
    concept: {
      heading: "¿Qué es el Ghost?",
      intro:
        "Los archivos digitales públicos del mundo contienen miles de millones de registros — sin embargo, lo que no dicen puede ser más revelador que lo que dicen. Cuando se analizan a través de múltiples archivos y disciplinas, emergen contradicciones que ningún registro o campo de estudio puede explicar por sí solo. El residuo inexplicable que persiste tras un análisis exhaustivo — la presencia sentida en la ausencia — eso es el Ghost.",
      principlesHeading: "Este sistema opera bajo cinco principios:",
      autonomousAgents: "Agentes de IA autónomos",
      autonomousAgentsDesc:
        "Investigación sin sesgo humano ni fatiga",
      transparency: "Transparencia radical",
      transparencyDesc:
        "Cada hipótesis construida sobre, y verificable a través de, registros públicos exclusivamente",
      crossDiscovery: "Descubrimiento cruzado impulsado por IA",
      crossDiscoveryDesc:
        "Anomalías visibles solo cuando se cruzan registros de diferentes archivos y disciplinas",
      interdisciplinary: "Análisis interdisciplinario",
      interdisciplinaryDesc:
        "Cinco campos académicos: Historia, Estudios del Folclore, Antropología Cultural, Lingüística y Ciencia Archivística",
      intellectualAwe: "Asombro intelectual",
      intellectualAweDesc:
        "Lo inexplicable como objeto legítimo de investigación académica, no sensacionalismo",
      folklore:
        "El folclore no es decoración. Es evidencia complementaria — el registro no oficial que llena los silencios dejados por la documentación oficial.",
    },
    methodology: {
      heading: "Cómo investigamos",
      intro:
        "Cada investigación sigue un proceso de seis pasos. El paso 1 utiliza un agente de IA para generar palabras clave de búsqueda, que luego se envían a las API de los archivos de forma programática. Los pasos 2–3 son operaciones programáticas deterministas — no interviene ninguna interpretación de IA. Los pasos 4–6 utilizan modelos de lenguaje grandes (LLMs) para el análisis, la síntesis y la generación narrativa.",
      programLabel: "PROGRAMA",
      llmLabel: "LLM",
      hybridLabel: "LLM + PROGRAMA",
      steps: {
        search: {
          title: "Búsqueda API",
          description: "Un agente de IA analiza el tema de investigación y genera palabras clave de búsqueda — tanto términos sistemáticos para la reproducibilidad como términos exploratorios para un descubrimiento más amplio. Estas palabras clave se envían de forma programática a las API de archivos digitales públicos — Trove, NDL Search, NYPL Digital Collections, Chronicling America, Internet Archive y Delpher — para recuperar metadatos y registros de catálogo.",
        },
        fulltext: {
          title: "Recuperación de texto completo",
          description: "Para cada registro devuelto, el sistema sigue las URL de origen para recuperar el texto completo de los documentos primarios. Se trata de una recuperación mecánica — no se realiza ningún resumen ni interpretación.",
        },
        excerpt: {
          title: "Extracción de fragmentos",
          description: "Se extraen pasajes relevantes de los documentos recuperados mediante coincidencia de palabras clave y heurísticas posicionales. Los fragmentos sin procesar se conservan textualmente para el análisis posterior.",
        },
        analysis: {
          title: "Análisis interdisciplinario",
          description: "Agentes Scholar específicos de cada idioma analizan los documentos recopilados a través de cinco perspectivas académicas: Historia, Estudios del Folclore, Antropología Cultural, Lingüística y Ciencia Archivística. Cada uno identifica contradicciones, anomalías y patrones dentro de su grupo lingüístico asignado.",
        },
        debate: {
          title: "Debate interdisciplinario",
          description: "Los agentes Scholar participan en un debate estructurado, cuestionando los hallazgos de los demás e identificando discrepancias que ningún análisis individual podría revelar.",
        },
        certification: {
          title: "Certificación Ghost",
          description: "El Armchair Polymath sintetiza todos los análisis y debates, aplicando los tres criterios de certificación Ghost: múltiples fuentes independientes, exclusión de limitaciones de API y reproducibilidad. El resultado se clasifica como Fantasma confirmado, Fantasma sospechado o Eco de archivo.",
        },
      },
    },
    storytellers: {
      heading: "Nuestros Narradores",
      intro:
        "Cada artículo de este archivo es escrito por un modelo de lenguaje de IA diferente — nuestros narradores. Diferentes modelos aportan diferentes perspectivas analíticas a la misma evidencia archivística.",
    },
  },
  detail: {
    returnToArchive: "Volver al archivo",
    archivalData: "Datos de archivo",
    archivalEvidence: "Evidencia de archivo",
    primarySource: "Fuente primaria",
    contrastingSource: "Fuente contrastante",
    additionalEvidence: "Evidencia adicional",
    published: "Publicado:",
    discoveredDiscrepancy: "Discrepancia descubierta",
    hypothesis: "Hipótesis",
    alternativeHypotheses: "Hipótesis alternativas:",
    historicalContext: "Contexto histórico",
    relatedEvents: "Eventos relacionados:",
    keyFigures: "Figuras clave:",
    storyAngles: "Ángulos narrativos",
    classificationNotice:
      "Este expediente representa un análisis generado por IA de registros de archivo. Todas las fuentes deben verificarse de forma independiente.",
    breadcrumbHome: "Inicio",
    tableOfContents: "Índice",
    tocNarrative: "Narrativa",
    tocDiscrepancy: "Discrepancia descubierta",
    tocEvidence: "Evidencia de archivo",
    tocHypothesis: "Hipótesis",
    tocHistoricalContext: "Contexto histórico",
    relatedArticles: "Expedientes relacionados",
    storytoldBy: "Narrado por",
  },
  evidence: {
    source: "Fuente",
    view: "Ver",
    originalText: "Texto original",
  },
  classification: {
    HIS: "Historia",
    FLK: "Folclore",
    ANT: "Antropología",
    OCC: "Ocultismo",
    URB: "Leyenda urbana",
    CRM: "Crimen",
    REL: "Religión",
    LOC: "Locus",
    moreLocations: "+{count} más",
  },
  siteIntro: {
    tagline: "Descubrimiento de anomalías impulsado por IA entre archivos y disciplinas",
    description:
      "Un sistema autónomo de agentes de IA que analiza los archivos digitales públicos del mundo a través de cinco disciplinas académicas — historia, folclore, antropología, lingüística y archivística — revelando contradicciones que ningún registro o campo de estudio puede explicar por sí solo.",
  },
  classificationGuide: {
    heading: "Índice de clasificación",
    descriptions: {
      HIS: "Discrepancias en registros históricos, personas desaparecidas, lagunas documentales",
      FLK: "Tradiciones locales, folclore oral, creencias populares",
      ANT: "Rituales, estructuras sociales, contacto intercultural",
      OCC: "Fenómenos inexplicables, eventos sobrenaturales",
      URB: "Rumores modernos, historias de fantasmas contemporáneas",
      CRM: "Crímenes sin resolver, desapariciones, muertes misteriosas",
      REL: "Tabúes religiosos, maldiciones, ritos prohibidos",
      LOC: "Anomalías ligadas a lugares, ubicaciones encantadas",
    },
  },
  share: {
    shareOnX: "Compartir en X",
    shareOnFacebook: "Compartir en Facebook",
    shareOnReddit: "Compartir en Reddit",
    copyLink: "Copiar enlace",
    linkCopied: "Enlace copiado!",
    shareThisArticle: "Compartir este expediente",
  },
  confidence: {
    confirmedGhost: "Fantasma confirmado",
    suspectedGhost: "Fantasma sospechado",
    archivalEcho: "Eco de archivo",
  },
  sourceCoverage: {
    heading: "Evaluación Ghost",
  },
  seo: {
    homeDescription: "Un sistema autónomo de agentes de IA que analiza los archivos digitales públicos del mundo a través de cinco disciplinas académicas — revelando anomalías que ningún registro o campo de estudio puede explicar por sí solo.",
    archiveDescription: "Índice completo de todas las anomalías, discrepancias y fenómenos inexplicables desenterrados de los registros públicos del mundo.",
    aboutDescription: "Descubre Ghost in the Archive — una unidad autónoma de investigación con IA que analiza los archivos digitales públicos del mundo a través de cinco disciplinas académicas: historia, folclore, antropología, lingüística y archivística.",
  },
  footer: {
    description:
      "Análisis impulsado por IA de los archivos digitales públicos del mundo — desenterrando los Fantasmas ocultos en las brechas entre registros, archivos y disciplinas.",
    primarySources: "Fuentes primarias",
    technical: "Técnico",
    classification: "Clasificación:",
    pendingApplication: "Solicitud pendiente",
    home: "Inicio",
    archive: "Archivo",
    about: "Acerca de",
  },
};

export default dict;
