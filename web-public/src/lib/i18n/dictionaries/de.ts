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
      "Alle Quellmaterialien stammen ausschließlich aus öffentlichen digitalen Archiven weltweit — der Library of Congress, DPLA, Europeana, dem Internet Archive und ähnlichen Institutionen in zahlreichen Ländern und Sprachen. Bei keiner Ermittlung werden Verschlusssachen verwendet. (Wir besitzen keine Sicherheitsfreigabe. Wir haben auch keine beantragt.)",
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
      coda:
        "Und ein ungeschriebenes Prinzip: Vergiss den Witz nicht. Die Archive sind schon Gräber genug.",
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
  footer: {
    description:
      "Mehrsprachige Kreuzanalyse der öffentlichen digitalen Archive der Welt — die Geister aufspüren, die sich in den Lücken zwischen Aufzeichnungen, Sprachen und Disziplinen verbergen.",
    primarySources: "Primärquellen",
    technical: "Technik",
    classification: "Klassifikation:",
  },
};

export default dict;
