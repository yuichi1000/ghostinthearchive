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
  };
  home: {
    latestDiscoveries: string;
    featuredStory: string;
    noMysteries: string;
    noMysteriesDesc: string;
    classifiedRedacted: string;
  };
  about: {
    title: string;
    heading: string;
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
  };
  evidence: {
    source: string;
    view: string;
    originalText: string;
  };
  footer: {
    description: string;
    primarySources: string;
    technical: string;
    classification: string;
  };
}
