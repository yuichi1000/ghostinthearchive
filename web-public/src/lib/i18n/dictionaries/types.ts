export interface Dictionary {
  hero: {
    badge: string;
    title: string;
    subtitle: string;
    description: string;
  };
  disclosure: {
    title: string;
    notice: string;
    paragraph1: string;
    paragraph2: string;
    paragraph3: string;
    footer: {
      verified: string;
      crossReferenced: string;
      accuracy: string;
    };
  };
  nav: {
    about: string;
    archive: string;
  };
  home: {
    latestDiscoveries: string;
    featuredStory: string;
    noMysteries: string;
    noMysteriesDesc: string;
    classifiedRedacted: string;
    viewAllArticles: string;
  };
  archive: {
    title: string;
    heading: string;
    description: string;
    noArticles: string;
    page: string;
    previous: string;
    next: string;
  };
  about: {
    title: string;
    heading: string;
    concept: {
      heading: string;
      intro: string;
      principlesHeading: string;
      autonomousAgents: string;
      autonomousAgentsDesc: string;
      transparency: string;
      transparencyDesc: string;
      crossDiscovery: string;
      crossDiscoveryDesc: string;
      interdisciplinary: string;
      interdisciplinaryDesc: string;
      intellectualAwe: string;
      intellectualAweDesc: string;
      folklore: string;
      coda: string;
    };
  };
  detail: {
    returnToArchive: string;
    archivalData: string;
    archivalEvidence: string;
    primarySource: string;
    contrastingSource: string;
    additionalEvidence: string;
    published: string;
    discoveredDiscrepancy: string;
    hypothesis: string;
    alternativeHypotheses: string;
    historicalContext: string;
    relatedEvents: string;
    keyFigures: string;
    storyAngles: string;
    classificationNotice: string;
    breadcrumbHome: string;
    tableOfContents: string;
    tocNarrative: string;
    tocDiscrepancy: string;
    tocEvidence: string;
    tocHypothesis: string;
    tocHistoricalContext: string;
    relatedArticles: string;
  };
  evidence: {
    source: string;
    view: string;
    originalText: string;
  };
  classification: {
    HIS: string;
    FLK: string;
    ANT: string;
    OCC: string;
    URB: string;
    CRM: string;
    REL: string;
    LOC: string;
    moreLocations: string;
  };
  share: {
    shareOnX: string;
    shareOnFacebook: string;
    shareOnReddit: string;
    copyLink: string;
    linkCopied: string;
    shareThisArticle: string;
  };
  footer: {
    description: string;
    primarySources: string;
    technical: string;
    classification: string;
  };
}
