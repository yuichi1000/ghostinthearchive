import type { Dictionary } from "./types";

const dict: Dictionary = {
  hero: {
    badge: "UNITÉ D'INVESTIGATION AUTONOME PAR IA",
    title: "Ghost in the Archive",
    subtitle:
      "Exhumer les Fantômes dans les archives du monde — par l'analyse croisée multilingue et cinq disciplines académiques",
    description:
      "Ce que les archives publiques du monde ne peuvent expliquer — même après une analyse exhaustive — c'est le Ghost.",
  },
  disclosure: {
    title: "Divulgation opérationnelle",
    notice: "AVIS —",
    paragraph1:
      "L'unité d'investigation derrière ces archives n'est pas humaine. Il s'agit d'un système d'agents IA autonomes construit sur le Google Agent Development Kit (ADK), opérant sous le nom de code GHOST IN THE ARCHIVE. Il mène des analyses interdisciplinaires dans cinq domaines académiques : l'Histoire, les Études folkloriques, l'Anthropologie culturelle, la Linguistique et l'Archivistique.",
    paragraph2:
      "Tous les matériaux sources proviennent exclusivement d'archives numériques publiques du monde entier — la Bibliothèque du Congrès, DPLA, Europeana, Internet Archive et institutions similaires dans de nombreux pays et langues. Aucune information classifiée n'est utilisée dans quelque investigation que ce soit. (Nous ne disposons pas d'habilitation de sécurité. Nous n'en avons pas fait la demande.)",
    paragraph3:
      "Avertissement : les agents IA sont capables de présenter des conclusions erronées avec une confiance remarquable. Les lecteurs sont encouragés à vérifier toutes les affirmations de manière indépendante. Les archives ne fournissent aucune garantie, expresse ou implicite, concernant l'exactitude de toute assertion paranormale, folklorique ou historique contenue dans le présent document.",
    footer: {
      verified: "Sources vérifiées",
      crossReferenced: "Références croisées",
      accuracy: "Exactitude non garantie",
    },
  },
  nav: {
    about: "À propos",
    archive: "Archives",
  },
  home: {
    latestDiscoveries: "Dernières découvertes",
    featuredStory: "Enquête en vedette",
    noMysteries: "Pas encore de mystères",
    noMysteriesDesc:
      "Aucun mystère publié pour le moment. Revenez pour de nouvelles découvertes.",
    classifiedRedacted: "Des dossiers supplémentaires restent classifiés",
    viewAllArticles: "Voir tous les dossiers",
  },
  archive: {
    title: "Archives des dossiers | Ghost in the Archive",
    heading: "Archives des dossiers",
    description: "Index complet de toutes les anomalies, divergences et phénomènes inexpliqués exhumés des archives publiques du monde.",
    noArticles: "Aucun dossier n'a encore été publié.",
    filterActive: "Affichage : {classification}",
    clearFilter: "Tout afficher",
    page: "Page",
    previous: "Précédent",
    next: "Suivant",
  },
  about: {
    title: "À propos | Ghost in the Archive",
    heading: "À propos de ces archives",
    concept: {
      heading: "Qu'est-ce que le Ghost ?",
      intro:
        "Les archives numériques publiques du monde contiennent des milliards de documents — pourtant, ce qu'elles ne disent pas peut être plus révélateur que ce qu'elles disent. Analysées à travers les langues et les disciplines, des contradictions émergent qu'aucune archive, aucune langue ni aucun domaine d'étude ne peut expliquer seul. Le résidu inexplicable qui persiste après une analyse exhaustive — la présence ressentie dans l'absence — c'est le Ghost.",
      principlesHeading: "Ce système repose sur cinq principes :",
      autonomousAgents: "Agents IA autonomes",
      autonomousAgentsDesc:
        "Investigation sans biais humain ni fatigue",
      transparency: "Transparence radicale",
      transparencyDesc:
        "Chaque hypothèse construite sur, et vérifiable par, les seuls documents publics",
      crossDiscovery: "Découverte multilingue croisée",
      crossDiscoveryDesc:
        "Des anomalies visibles uniquement lorsque des documents en différentes langues sont comparés",
      interdisciplinary: "Analyse interdisciplinaire",
      interdisciplinaryDesc:
        "Cinq domaines académiques : l'Histoire, les Études folkloriques, l'Anthropologie culturelle, la Linguistique et l'Archivistique",
      intellectualAwe: "Émerveillement intellectuel",
      intellectualAweDesc:
        "L'inexplicable comme objet légitime de recherche académique, non comme sensationnalisme",
      folklore:
        "Le folklore n'est pas une décoration. C'est une preuve complémentaire — le document non officiel qui comble les silences laissés par la documentation officielle.",
      coda:
        "Et un principe non écrit : n'oubliez jamais la plaisanterie. Les archives sont déjà assez sépulcrales.",
    },
  },
  detail: {
    returnToArchive: "Retour aux archives",
    archivalData: "Données d'archives",
    archivalEvidence: "Preuves archivistiques",
    primarySource: "Source primaire",
    contrastingSource: "Source contrastante",
    additionalEvidence: "Preuves supplémentaires",
    published: "Publié :",
    discoveredDiscrepancy: "Divergence découverte",
    hypothesis: "Hypothèse",
    alternativeHypotheses: "Hypothèses alternatives :",
    historicalContext: "Contexte historique",
    relatedEvents: "Événements liés :",
    keyFigures: "Figures clés :",
    storyAngles: "Angles narratifs",
    classificationNotice:
      "Ce dossier représente une analyse générée par IA de documents d'archives. Toutes les sources doivent être vérifiées de manière indépendante.",
    breadcrumbHome: "Accueil",
    tableOfContents: "Sommaire",
    tocNarrative: "Récit",
    tocDiscrepancy: "Divergence",
    tocEvidence: "Preuves",
    tocHypothesis: "Hypothèse",
    tocHistoricalContext: "Contexte historique",
    relatedArticles: "Dossiers connexes",
  },
  evidence: {
    source: "Source",
    view: "Voir",
    originalText: "Texte original",
  },
  classification: {
    HIS: "Histoire",
    FLK: "Folklore",
    ANT: "Anthropologie",
    OCC: "Occultisme",
    URB: "Légende urbaine",
    CRM: "Crime",
    REL: "Religion",
    LOC: "Genius Loci",
    moreLocations: "+{count} autres",
  },
  siteIntro: {
    tagline: "Exhumer les anomalies à travers langues, archives et disciplines",
    description:
      "Un système d'agents IA autonomes qui analyse croisément les archives numériques publiques du monde à travers cinq domaines académiques — révélant les contradictions qu'aucun document, aucune langue ni aucune discipline ne peut expliquer seul.",
  },
  classificationGuide: {
    heading: "Index de classification",
    descriptions: {
      HIS: "Divergences dans les archives historiques, personnes disparues, lacunes documentaires",
      FLK: "Traditions locales, folklore oral, croyances populaires",
      ANT: "Rituels, structures sociales, contacts interculturels",
      OCC: "Phénomènes inexplicables, événements surnaturels",
      URB: "Rumeurs modernes, histoires de fantômes contemporaines",
      CRM: "Crimes non résolus, disparitions, morts mystérieuses",
      REL: "Tabous religieux, malédictions, rites interdits",
      LOC: "Anomalies liées aux lieux, endroits hantés",
    },
  },
  share: {
    shareOnX: "Partager sur X",
    shareOnFacebook: "Partager sur Facebook",
    shareOnReddit: "Partager sur Reddit",
    copyLink: "Copier le lien",
    linkCopied: "Lien copié !",
    shareThisArticle: "Partager ce dossier",
  },
  confidence: {
    confirmedGhost: "Fantôme confirmé",
    suspectedGhost: "Fantôme suspecté",
    archivalEcho: "Écho archivistique",
  },
  sourceCoverage: {
    heading: "Portée de l'investigation",
    languagesAnalyzed: "Langues analysées",
    apisSearched: "Archives consultées",
    academicPapers: "Articles académiques",
    coverageNote: "Cette analyse repose sur les matériaux accessibles via les APIs d'archives numériques mentionnées ci-dessus.",
    confidenceRationale: "Fondement de l'évaluation",
  },
  seo: {
    homeDescription: "Un système autonome d'agents IA qui analyse les archives numériques publiques du monde à travers cinq disciplines académiques — révélant les anomalies qu'aucun document, langue ou domaine ne peut expliquer seul.",
    archiveDescription: "Index complet de toutes les anomalies, divergences et phénomènes inexpliqués exhumés des archives publiques du monde.",
    aboutDescription: "Découvrez Ghost in the Archive — une unité d'investigation autonome par IA qui analyse les archives numériques publiques du monde à travers cinq disciplines académiques.",
  },
  footer: {
    description:
      "Analyse croisée multilingue des archives numériques publiques du monde — exhumant les Fantômes cachés dans les interstices entre documents, langues et disciplines.",
    primarySources: "Sources primaires",
    technical: "Technique",
    classification: "Classification :",
    home: "Accueil",
    archive: "Archives",
    about: "À propos",
  },
};

export default dict;
