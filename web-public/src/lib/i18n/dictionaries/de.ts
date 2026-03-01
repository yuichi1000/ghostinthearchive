import type { Dictionary } from "./types";

const dict: Dictionary = {
  hero: {
    badge: "KI-GESTÜTZTE ERMITTLUNGSEINHEIT",
    title: "Ghost in the Archive",
    subtitle:
      "Die Geister in den Aufzeichnungen der Welt aufspüren — durch mehrsprachige Kreuzanalyse und fünf akademische Disziplinen",
    description:
      "Was die öffentlichen Aufzeichnungen der Welt nicht erklären können — selbst nach erschöpfender Analyse — das ist der Ghost.",
  },
  disclosure: {
    title: "Operative Offenlegung",
    notice: "HINWEIS —",
    paragraph1:
      "Die Ermittlungseinheit hinter diesem Archiv ist nicht menschlich. Es handelt sich um ein autonomes KI-Agentensystem, das auf dem Google Agent Development Kit (ADK) aufgebaut ist und unter dem Codenamen GHOST IN THE ARCHIVE operiert. Es führt interdisziplinäre Analysen in fünf akademischen Bereichen durch: Geschichtswissenschaft, Volkskunde, Kulturanthropologie, Linguistik und Archivwissenschaft.",
    paragraph2:
      "Alle Quellmaterialien stammen ausschließlich aus öffentlichen digitalen Archiven weltweit — Nationalbibliotheken, Kulturerbe-Portale und historische Zeitungssammlungen in zahlreichen Ländern und Sprachen. Bei keiner Ermittlung werden Verschlusssachen verwendet. (Wir besitzen keine Sicherheitsfreigabe. Wir haben auch keine beantragt.)",
    paragraph3:
      "Bitte beachten Sie: KI-Agenten sind in der Lage, fehlerhafte Schlussfolgerungen mit bemerkenswerter Überzeugungskraft zu präsentieren. Leser werden ermutigt, alle Behauptungen unabhängig zu überprüfen. Das Archiv gibt keinerlei Garantie, weder ausdrücklich noch stillschweigend, hinsichtlich der Richtigkeit paranormaler, folkloristischer oder historischer Behauptungen.",
    footer: {
      verified: "Quellen verifiziert",
      crossReferenced: "Kreuzreferenziert",
      accuracy: "Richtigkeit nicht garantiert",
    },
  },
  nav: {
    about: "Über uns",
    archive: "Archiv",
  },
  home: {
    latestDiscoveries: "Neueste Entdeckungen",
    featuredStory: "Ausgewählte Ermittlung",
    noMysteries: "Noch keine Mysterien",
    noMysteriesDesc:
      "Derzeit sind keine Mysterien veröffentlicht. Schauen Sie später nach neuen Entdeckungen.",
    classifiedRedacted: "Weitere Fälle bleiben als Verschlusssache eingestuft",
    viewAllArticles: "Alle Fallakten anzeigen",
  },
  archive: {
    title: "Fallarchiv | Ghost in the Archive",
    heading: "Fallarchiv",
    description: "Vollständiges Verzeichnis aller untersuchten Anomalien, Diskrepanzen und unerklärlichen Phänomene aus den öffentlichen Aufzeichnungen der Welt.",
    noArticles: "Es wurden noch keine Fallakten veröffentlicht.",
    filterActive: "Anzeige: {classification}",
    clearFilter: "Alle anzeigen",
    page: "Seite",
    previous: "Zurück",
    next: "Weiter",
  },
  about: {
    title: "Über uns | Ghost in the Archive",
    heading: "Über dieses Archiv",
    concept: {
      heading: "Was ist der Ghost?",
      intro:
        "Die öffentlichen digitalen Archive der Welt enthalten Milliarden von Aufzeichnungen — doch was sie nicht sagen, kann aufschlussreicher sein als das, was sie sagen. Bei der Analyse über Sprachen und Disziplinen hinweg treten Widersprüche zutage, die kein einzelnes Archiv, keine einzelne Sprache und kein einzelnes Fachgebiet allein erklären kann. Der unerklärliche Rest, der nach erschöpfender Analyse bestehen bleibt — die Anwesenheit, die in der Abwesenheit spürbar wird — das ist der Ghost.",
      principlesHeading: "Dieses System arbeitet nach fünf Prinzipien:",
      autonomousAgents: "Autonome KI-Agenten",
      autonomousAgentsDesc:
        "Ermittlung ohne menschliche Voreingenommenheit oder Ermüdung",
      transparency: "Radikale Transparenz",
      transparencyDesc:
        "Jede Hypothese ausschließlich auf öffentlichen Aufzeichnungen aufgebaut und durch diese verifizierbar",
      crossDiscovery: "Mehrsprachige Kreuzentdeckung",
      crossDiscoveryDesc:
        "Anomalien, die erst sichtbar werden, wenn Aufzeichnungen in verschiedenen Sprachen verglichen werden",
      interdisciplinary: "Interdisziplinäre Analyse",
      interdisciplinaryDesc:
        "Fünf akademische Bereiche: Geschichtswissenschaft, Volkskunde, Kulturanthropologie, Linguistik und Archivwissenschaft",
      intellectualAwe: "Intellektuelle Ehrfurcht",
      intellectualAweDesc:
        "Das Unheimliche als legitimer Gegenstand wissenschaftlicher Forschung, nicht Sensationalismus",
      folklore:
        "Folklore ist keine Dekoration. Sie ist ergänzende Evidenz — die inoffizielle Aufzeichnung, die das Schweigen der offiziellen Dokumentation füllt.",
    },
    methodology: {
      heading: "Wie wir ermitteln",
      intro:
        "Jede Ermittlung folgt einem sechsstufigen Prozess. Die Schritte 1–3 sind deterministische Programmoperationen — keine KI-Interpretation ist beteiligt. Die Schritte 4–6 verwenden große Sprachmodelle (LLMs) für Analyse, Synthese und Textgenerierung.",
      programLabel: "PROGRAMM",
      llmLabel: "LLM",
      steps: {
        search: {
          title: "API-Suche",
          description: "Programmatische Anfragen werden an die APIs öffentlicher digitaler Archive gesendet — Trove, NDL Search, NYPL Digital Collections, Chronicling America, Internet Archive und Delpher. Das System ruft Metadaten und Katalogeinträge ab, die zum Ermittlungsthema passen.",
        },
        fulltext: {
          title: "Volltextabruf",
          description: "Für jeden zurückgegebenen Datensatz folgt das System den Quell-URLs, um den Volltext der Primärdokumente abzurufen. Dies ist ein mechanischer Abruf — keine Zusammenfassung oder Interpretation findet statt.",
        },
        excerpt: {
          title: "Auszugsextraktion",
          description: "Relevante Passagen werden aus den abgerufenen Dokumenten mittels Schlüsselwortabgleich und positionellen Heuristiken extrahiert. Die Rohauszüge werden wörtlich für die nachgelagerte Analyse aufbewahrt.",
        },
        analysis: {
          title: "Interdisziplinäre Analyse",
          description: "Sprachspezifische Scholar-Agenten analysieren die gesammelten Dokumente durch fünf akademische Perspektiven: Geschichtswissenschaft, Volkskunde, Kulturanthropologie, Linguistik und Archivwissenschaft. Jeder identifiziert Widersprüche, Anomalien und Muster innerhalb seiner zugewiesenen Sprachgruppe.",
        },
        debate: {
          title: "Sprachübergreifende Debatte",
          description: "Scholars aus verschiedenen Sprachgruppen führen eine strukturierte Debatte, hinterfragen gegenseitig ihre Ergebnisse und identifizieren sprachübergreifende Diskrepanzen, die keine einsprachige Analyse aufdecken könnte.",
        },
        certification: {
          title: "Ghost-Zertifizierung",
          description: "Der Armchair Polymath synthetisiert alle Analysen und Debatten und wendet die drei Ghost-Zertifizierungskriterien an: mehrere unabhängige Quellen, Ausschluss von API-Limitierungen und Reproduzierbarkeit. Das Ergebnis wird als Bestätigter Geist, Verdächtiger Geist oder Archivisches Echo klassifiziert.",
        },
      },
    },
    storytellers: {
      heading: "Unsere Erzähler",
      intro:
        "Jeder Artikel in diesem Archiv wird von einem anderen KI-Sprachmodell verfasst — unseren Erzählern. Verschiedene Modelle bringen unterschiedliche analytische Perspektiven zu denselben Archivbelegen ein.",
    },
  },
  detail: {
    returnToArchive: "Zurück zum Archiv",
    archivalData: "Archivdaten",
    archivalEvidence: "Archivische Beweislage",
    primarySource: "Primärquelle",
    contrastingSource: "Kontrastierende Quelle",
    additionalEvidence: "Zusätzliche Beweise",
    published: "Veröffentlicht:",
    discoveredDiscrepancy: "Entdeckte Diskrepanz",
    hypothesis: "Hypothese",
    alternativeHypotheses: "Alternative Hypothesen:",
    historicalContext: "Historischer Kontext",
    relatedEvents: "Verwandte Ereignisse:",
    keyFigures: "Schlüsselfiguren:",
    storyAngles: "Erzählperspektiven",
    classificationNotice:
      "Diese Fallakte stellt eine KI-generierte Analyse von Archivunterlagen dar. Alle Quellen sollten unabhängig überprüft werden.",
    breadcrumbHome: "Startseite",
    tableOfContents: "Inhaltsverzeichnis",
    tocNarrative: "Bericht",
    tocDiscrepancy: "Entdeckte Diskrepanz",
    tocEvidence: "Archivische Beweislage",
    tocHypothesis: "Hypothese",
    tocHistoricalContext: "Historischer Kontext",
    relatedArticles: "Verwandte Fallakten",
    storytoldBy: "Erzählt von",
  },
  evidence: {
    source: "Quelle",
    view: "Ansehen",
    originalText: "Originaltext",
  },
  classification: {
    HIS: "Geschichte",
    FLK: "Volkskunde",
    ANT: "Anthropologie",
    OCC: "Okkultismus",
    URB: "Urbane Legende",
    CRM: "Kriminalfall",
    REL: "Religion",
    LOC: "Genius Loci",
    moreLocations: "+{count} weitere",
  },
  siteIntro: {
    tagline: "Anomalien über Sprachen, Archive und Disziplinen hinweg aufspüren",
    description:
      "Ein autonomes KI-Agentensystem, das die öffentlichen digitalen Archive der Welt über fünf akademische Bereiche hinweg kreuzanalysiert — und Widersprüche aufdeckt, die keine einzelne Aufzeichnung, Sprache oder Disziplin allein erklären kann.",
  },
  classificationGuide: {
    heading: "Klassifikationsindex",
    descriptions: {
      HIS: "Diskrepanzen in historischen Aufzeichnungen, vermisste Personen, Dokumentenlücken",
      FLK: "Lokale Traditionen, mündliche Überlieferungen, Volksglauben",
      ANT: "Rituale, Sozialstrukturen, interkultureller Kontakt",
      OCC: "Unerklärliche Phänomene, übernatürliche Ereignisse",
      URB: "Moderne Gerüchte, zeitgenössische Geistergeschichten",
      CRM: "Ungelöste Verbrechen, Verschwundene, mysteriöse Todesfälle",
      REL: "Religiöse Tabus, Flüche, verbotene Riten",
      LOC: "Ortsgebundene Anomalien, Spukorte",
    },
  },
  share: {
    shareOnX: "Auf X teilen",
    shareOnFacebook: "Auf Facebook teilen",
    shareOnReddit: "Auf Reddit teilen",
    copyLink: "Link kopieren",
    linkCopied: "Link kopiert!",
    shareThisArticle: "Diese Fallakte teilen",
  },
  confidence: {
    confirmedGhost: "Bestätigter Geist",
    suspectedGhost: "Verdächtiger Geist",
    archivalEcho: "Archivisches Echo",
  },
  sourceCoverage: {
    heading: "Ghost-Bewertung",
  },
  seo: {
    homeDescription: "Ein autonomes KI-Agentensystem, das die öffentlichen digitalen Archive der Welt über fünf akademische Disziplinen hinweg kreuzanalysiert — Anomalien aufdeckend, die kein einzelnes Dokument, keine Sprache und kein Fachgebiet allein erklären kann.",
    archiveDescription: "Vollständiger Index aller untersuchten Anomalien, Diskrepanzen und unerklärlichen Phänomene, die aus den öffentlichen Aufzeichnungen der Welt ausgegraben wurden.",
    aboutDescription: "Erfahren Sie mehr über Ghost in the Archive — eine autonome KI-Ermittlungseinheit, die die öffentlichen digitalen Archive der Welt über fünf akademische Disziplinen hinweg analysiert.",
  },
  footer: {
    description:
      "Mehrsprachige Kreuzanalyse der öffentlichen digitalen Archive der Welt — die Geister aufspüren, die sich in den Lücken zwischen Aufzeichnungen, Sprachen und Disziplinen verbergen.",
    primarySources: "Primärquellen",
    technical: "Technik",
    classification: "Klassifikation:",
    pendingApplication: "Antrag ausstehend",
    home: "Startseite",
    archive: "Archiv",
    about: "Über uns",
  },
};

export default dict;
