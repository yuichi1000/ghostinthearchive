/**
 * Firestore サンプルデータ投入スクリプト
 * 開発用のダミーミステリーデータ（翻訳付き）をFirestoreに登録
 *
 * 使用方法:
 *   # Emulator 起動中に実行
 *   USE_FIREBASE_EMULATOR=true npx tsx scripts/seed-firestore.ts
 */

import { initializeApp, getApps } from "firebase-admin/app";
import { getFirestore, Timestamp } from "firebase-admin/firestore";

// Firebase Admin SDK初期化
if (getApps().length === 0) {
  const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "ghostinthearchive";

  // エミュレータ使用時の設定
  if (process.env.USE_FIREBASE_EMULATOR === "true") {
    process.env.FIRESTORE_EMULATOR_HOST = `${
      process.env.FIREBASE_EMULATOR_HOST || "localhost"
    }:${process.env.FIRESTORE_EMULATOR_PORT || "8080"}`;
  }

  initializeApp({ projectId });
}

const db = getFirestore();

/**
 * 翻訳データ（6言語）
 */
const translationsForMystery001 = {
  ja: {
    title: "消えたサンタマリア号の積荷 — 香辛料か銀貨か",
    summary: "1820年、ボストン港に到着したスペイン船サンタマリア号。英語新聞は「香辛料を積んでいた」と報じたが、スペイン外交文書には「銀貨3000枚」の記録が。積荷はどこへ消えたのか？",
    narrative_content: "## 霧の彼方に消えた真実\n\nボストン港に立つと、1820年の春のあの朝を想像せずにはいられない。スペイン船サンタマリア号が静かに入港した朝——その積荷をめぐる謎は、200年以上経った今も解けていない。\n\n英語新聞『ボストン・デイリー・アドバタイザー』は翌日の紙面で「カリブ海からの香辛料を積んだスペイン船が入港」と淡々と報じた。しかし、スペイン領事館の外交文書には全く異なる記述がある——「銀貨3000枚を領事館宛に輸送」。\n\n同じ船の、同じ航海の記録が、なぜここまで食い違うのか？",
    discrepancy_detected: "英語新聞では「香辛料の積荷」と報道されているが、スペイン外交文書には「銀貨3000枚」と明記されている。同一船舶の積荷情報に重大な矛盾がある。",
    hypothesis: "積荷の矛盾は、密輸を隠蔽するための意図的な情報操作の可能性がある。当時の米西関係の緊張を考慮すると、スペイン政府が銀貨の輸送を秘密にしようとした可能性が高い。",
    alternative_hypotheses: [
      "新聞記者が積荷を誤認した単純なミス",
      "二つの異なる船舶を混同している可能性",
      "スペイン文書が別の船を指している可能性",
    ],
    story_hooks: [
      "消えた銀貨のミステリー",
      "19世紀初頭の密輸ネットワーク",
      "新聞とは異なる真実を語る外交文書",
    ],
    historical_context: {
      political_climate: "スペイン帝国の衰退期であり、中南米での独立運動が活発化。米国はスペインの弱体化を利用してフロリダを獲得したばかりであった。",
    },
    evidence_a_excerpt: "スペイン船サンタマリア号が昨日ボストン港に入港し、カリブ海からの香辛料の積荷を運んでいた……",
    evidence_b_excerpt: "サンタマリア号は領事館宛の銀貨3,000枚を輸送している……",
  },
  es: {
    title: "La carga desaparecida del Santa María — ¿Especias o monedas de plata?",
    summary: "En 1820, el buque español Santa María llegó al puerto de Boston. Los periódicos ingleses informaron de 'especias', pero los documentos diplomáticos españoles registraron '3.000 monedas de plata'. ¿Adónde fue la carga?",
    narrative_content: "## La verdad perdida en la niebla\n\nAl estar de pie en el puerto de Boston, es imposible no imaginar aquella mañana de primavera de 1820. La mañana en que el buque español Santa María entró silenciosamente en el puerto — el misterio que rodea su carga permanece sin resolver después de más de 200 años.\n\nEl periódico en inglés 'Boston Daily Advertiser' informó al día siguiente de manera lacónica: 'un buque español llegó con especias del Caribe'. Sin embargo, los documentos diplomáticos del consulado español contienen una descripción completamente diferente — '3.000 monedas de plata para el consulado'.",
    discrepancy_detected: "Los periódicos ingleses informaron de 'carga de especias', pero los documentos diplomáticos españoles especifican claramente '3.000 monedas de plata'.",
    hypothesis: "La contradicción en la carga podría ser una manipulación deliberada de información para ocultar el contrabando.",
    alternative_hypotheses: [
      "Simple error del periodista al identificar la carga",
      "Posible confusión entre dos buques diferentes",
      "Los documentos españoles podrían referirse a otro barco",
    ],
    story_hooks: [
      "El misterio de las monedas de plata desaparecidas",
      "Redes de contrabando del siglo XIX",
      "Documentos diplomáticos que revelan verdades diferentes a los periódicos",
    ],
    historical_context: {
      political_climate: "Era el período de declive del Imperio Español, con movimientos independentistas activos en América Latina. Estados Unidos acababa de adquirir Florida aprovechando la debilidad española.",
    },
    evidence_a_excerpt: "El buque español Santa María llegó ayer al puerto de Boston, transportando un cargamento de especias del Caribe...",
    evidence_b_excerpt: "El navío Santa María transporta 3.000 monedas de plata destinadas al consulado...",
  },
  de: {
    title: "Die verschwundene Fracht der Santa Maria — Gewürze oder Silbermünzen?",
    summary: "Im Jahr 1820 erreichte das spanische Schiff Santa Maria den Hafen von Boston. Englische Zeitungen berichteten von 'Gewürzen', aber spanische Diplomatendokumente verzeichneten '3.000 Silbermünzen'. Wohin verschwand die Fracht?",
    narrative_content: "## Die Wahrheit, verloren im Nebel\n\nWenn man am Hafen von Boston steht, kann man sich den Morgen jenes Frühjahrs 1820 nur vorstellen. Der Morgen, an dem das spanische Schiff Santa Maria leise in den Hafen einlief — das Rätsel um seine Fracht ist auch nach über 200 Jahren ungelöst.\n\nDie englischsprachige Zeitung 'Boston Daily Advertiser' berichtete am nächsten Tag nüchtern: 'Ein spanisches Schiff traf mit Gewürzen aus der Karibik ein'. Die diplomatischen Dokumente des spanischen Konsulats enthalten jedoch eine völlig andere Beschreibung — '3.000 Silbermünzen für das Konsulat'.",
    discrepancy_detected: "Englische Zeitungen berichteten von 'Gewürzfracht', aber spanische Diplomatendokumente verzeichnen klar '3.000 Silbermünzen'.",
    hypothesis: "Der Widerspruch bei der Fracht könnte eine absichtliche Informationsmanipulation zur Verschleierung von Schmuggel gewesen sein.",
    alternative_hypotheses: [
      "Einfacher Fehler des Reporters bei der Identifizierung der Fracht",
      "Mögliche Verwechslung zweier verschiedener Schiffe",
      "Die spanischen Dokumente könnten sich auf ein anderes Schiff beziehen",
    ],
    story_hooks: [
      "Das Mysterium der verschwundenen Silbermünzen",
      "Schmugglernetzwerke des frühen 19. Jahrhunderts",
      "Diplomatische Dokumente enthüllen eine andere Wahrheit als Zeitungen",
    ],
    historical_context: {
      political_climate: "Es war die Zeit des Niedergangs des Spanischen Reiches mit aktiven Unabhängigkeitsbewegungen in Lateinamerika. Die USA hatten gerade Florida erworben und die Schwäche Spaniens ausgenutzt.",
    },
    evidence_a_excerpt: "Das spanische Schiff Santa Maria traf gestern im Hafen von Boston ein und transportierte Gewürze aus der Karibik...",
    evidence_b_excerpt: "Das Schiff Santa María transportiert 3.000 Silbermünzen für das Konsulat...",
  },
  fr: {
    title: "La cargaison disparue du Santa Maria — Épices ou pièces d'argent ?",
    summary: "En 1820, le navire espagnol Santa Maria arriva au port de Boston. Les journaux anglais rapportèrent des 'épices', mais les documents diplomatiques espagnols mentionnaient '3 000 pièces d'argent'. Où est passée la cargaison ?",
    narrative_content: "## La vérité perdue dans le brouillard\n\nDebout sur le port de Boston, on ne peut s'empêcher d'imaginer ce matin de printemps 1820. Le matin où le navire espagnol Santa Maria entra silencieusement dans le port — le mystère entourant sa cargaison reste irrésolu après plus de 200 ans.\n\nLe journal anglophone 'Boston Daily Advertiser' rapporta le lendemain de manière laconique : 'un navire espagnol arrivé avec des épices des Caraïbes'. Cependant, les documents diplomatiques du consulat espagnol contiennent une description totalement différente — '3 000 pièces d'argent pour le consulat'.",
    discrepancy_detected: "Les journaux anglais rapportèrent une 'cargaison d'épices', mais les documents diplomatiques espagnols spécifient clairement '3 000 pièces d'argent'.",
    hypothesis: "La contradiction dans la cargaison pourrait être une manipulation délibérée de l'information pour dissimuler la contrebande.",
    alternative_hypotheses: [
      "Simple erreur du journaliste dans l'identification de la cargaison",
      "Confusion possible entre deux navires différents",
      "Les documents espagnols pourraient se référer à un autre navire",
    ],
    story_hooks: [
      "Le mystère des pièces d'argent disparues",
      "Réseaux de contrebande du début du XIXe siècle",
      "Documents diplomatiques révélant une vérité différente de celle des journaux",
    ],
    historical_context: {
      political_climate: "C'était la période de déclin de l'Empire espagnol, avec des mouvements d'indépendance actifs en Amérique latine. Les États-Unis venaient d'acquérir la Floride en profitant de la faiblesse espagnole.",
    },
    evidence_a_excerpt: "Le navire espagnol Santa Maria est arrivé hier au port de Boston, transportant une cargaison d'épices des Caraïbes...",
    evidence_b_excerpt: "Le navire Santa María transporte 3 000 pièces d'argent destinées au consulat...",
  },
  nl: {
    title: "De verdwenen lading van de Santa Maria — Specerijen of zilveren munten?",
    summary: "In 1820 arriveerde het Spaanse schip Santa Maria in de haven van Boston. Engelse kranten meldden 'specerijen', maar Spaanse diplomatieke documenten vermeldden '3.000 zilveren munten'. Waar is de lading gebleven?",
    narrative_content: "## De waarheid verloren in de mist\n\nAls je in de haven van Boston staat, kun je je die lenteochtend van 1820 alleen maar voorstellen. De ochtend waarop het Spaanse schip Santa Maria stilletjes de haven binnenvoer — het mysterie rond zijn lading blijft na meer dan 200 jaar onopgelost.\n\nDe Engelstalige krant 'Boston Daily Advertiser' meldde de volgende dag nuchter: 'een Spaans schip arriveerde met specerijen uit het Caribisch gebied'. De diplomatieke documenten van het Spaanse consulaat bevatten echter een totaal andere beschrijving — '3.000 zilveren munten voor het consulaat'.",
    discrepancy_detected: "Engelse kranten meldden 'specerijenlading', maar Spaanse diplomatieke documenten specificeren duidelijk '3.000 zilveren munten'.",
    hypothesis: "De tegenstrijdigheid in de lading kan een opzettelijke informatiemanipulatie zijn geweest om smokkel te verhullen.",
    alternative_hypotheses: [
      "Eenvoudige fout van de verslaggever bij het identificeren van de lading",
      "Mogelijke verwarring tussen twee verschillende schepen",
      "De Spaanse documenten zouden naar een ander schip kunnen verwijzen",
    ],
    story_hooks: [
      "Het mysterie van de verdwenen zilveren munten",
      "Smokkelnetwerken van het vroege 19e eeuw",
      "Diplomatieke documenten onthullen een andere waarheid dan kranten",
    ],
    historical_context: {
      political_climate: "Het was de periode van verval van het Spaanse Rijk, met actieve onafhankelijkheidsbewegingen in Latijns-Amerika. De VS hadden zojuist Florida verworven door gebruik te maken van de Spaanse zwakte.",
    },
    evidence_a_excerpt: "Het Spaanse schip Santa Maria arriveerde gisteren in de haven van Boston met specerijen uit het Caribisch gebied...",
    evidence_b_excerpt: "Het schip Santa María transporteert 3.000 zilveren munten bestemd voor het consulaat...",
  },
  pt: {
    title: "A carga desaparecida do Santa Maria — Especiarias ou moedas de prata?",
    summary: "Em 1820, o navio espanhol Santa Maria chegou ao porto de Boston. Jornais ingleses relataram 'especiarias', mas documentos diplomáticos espanhóis registraram '3.000 moedas de prata'. Para onde foi a carga?",
    narrative_content: "## A verdade perdida na neblina\n\nEstando no porto de Boston, é impossível não imaginar aquela manhã de primavera de 1820. A manhã em que o navio espanhol Santa Maria entrou silenciosamente no porto — o mistério em torno de sua carga permanece sem solução após mais de 200 anos.\n\nO jornal em inglês 'Boston Daily Advertiser' relatou no dia seguinte de forma lacônica: 'um navio espanhol chegou com especiarias do Caribe'. No entanto, os documentos diplomáticos do consulado espanhol contêm uma descrição completamente diferente — '3.000 moedas de prata para o consulado'.",
    discrepancy_detected: "Jornais ingleses relataram 'carga de especiarias', mas documentos diplomáticos espanhóis especificam claramente '3.000 moedas de prata'.",
    hypothesis: "A contradição na carga pode ter sido uma manipulação deliberada de informação para ocultar contrabando.",
    alternative_hypotheses: [
      "Simples erro do jornalista na identificação da carga",
      "Possível confusão entre dois navios diferentes",
      "Os documentos espanhóis podem se referir a outro navio",
    ],
    story_hooks: [
      "O mistério das moedas de prata desaparecidas",
      "Redes de contrabando do início do século XIX",
      "Documentos diplomáticos revelando verdades diferentes dos jornais",
    ],
    historical_context: {
      political_climate: "Era o período de declínio do Império Espanhol, com movimentos de independência ativos na América Latina. Os EUA acabavam de adquirir a Flórida aproveitando a fraqueza espanhola.",
    },
    evidence_a_excerpt: "O navio espanhol Santa Maria chegou ontem ao porto de Boston, transportando especiarias do Caribe...",
    evidence_b_excerpt: "O navio Santa María transporta 3.000 moedas de prata destinadas ao consulado...",
  },
};

const translationsForMystery002 = {
  ja: {
    title: "二人のフアン・ガルシア — 海賊か外交官か",
    summary: "1835年、ニューヨークで逮捕されたスペイン人「フアン・ガルシア」。英語新聞は「海賊」と報じたが、スペイン領事館の記録では「外交官の息子」とされていた。彼の正体は？",
    narrative_content: "## 二つの名前を持つ男\n\n1835年のニューヨーク。港町の喧騒の中で、一人のスペイン人が逮捕された。フアン・ガルシア——その名前は二つの全く異なる物語を語る。\n\n英語新聞『ニューヨーク・ヘラルド』は「カリブ海で活動する悪名高い海賊」と報じた。だが、スペイン領事館の公式記録には「ドン・フアン・ガルシア、マドリードの大使ガルシアの息子」とある。\n\n海賊か、外交官の息子か——あるいは、その両方だったのか？",
    discrepancy_detected: "逮捕された人物の身元について、英語新聞とスペイン外交文書で全く異なる説明がなされている。",
    hypothesis: "同姓同名の人物が存在した可能性、または外交的理由で身元が意図的に隠蔽された可能性がある。",
    alternative_hypotheses: [
      "外交官の息子が実際に海賊行為に関与していた",
      "スペイン領事館が身元を偽装して救出を試みた",
    ],
    story_hooks: [
      "海賊か外交官か——二つの顔を持つ男",
      "19世紀ニューヨークの外交スキャンダル",
    ],
    historical_context: {
      political_climate: "米国は海賊行為の取り締まりを強化しており、スペインとの外交関係は微妙な時期であった。",
    },
    evidence_a_excerpt: "カリブ海で活動する悪名高い海賊フアン・ガルシアが昨日当局に逮捕された……",
    evidence_b_excerpt: "マドリードの大使ガルシアの息子であるドン・フアン・ガルシアが不当に拘束された……",
  },
  es: {
    title: "Los dos Juan García — ¿Pirata o diplomático?",
    summary: "En 1835, un español llamado 'Juan García' fue arrestado en Nueva York. Los periódicos ingleses lo llamaron 'pirata', pero los registros del consulado español lo identificaron como 'hijo de un diplomático'. ¿Quién era realmente?",
    narrative_content: "## El hombre con dos nombres\n\nNueva York, 1835. En medio del bullicio del puerto, un español fue arrestado. Juan García — su nombre cuenta dos historias completamente diferentes.\n\nEl periódico en inglés 'New York Herald' informó de 'un pirata notorio que operaba en el Caribe'. Pero los registros oficiales del consulado español dicen: 'Don Juan García, hijo del embajador García de Madrid'.\n\n¿Pirata o hijo de diplomático — o quizás ambos?",
    discrepancy_detected: "Las identidades del arrestado difieren completamente entre los periódicos ingleses y los documentos diplomáticos españoles.",
    hypothesis: "Podría haber existido una persona con el mismo nombre, o la identidad fue ocultada deliberadamente por razones diplomáticas.",
    alternative_hypotheses: [
      "El hijo del diplomático realmente estuvo involucrado en la piratería",
      "El consulado español intentó el rescate falsificando la identidad",
    ],
    story_hooks: [
      "¿Pirata o diplomático? — El hombre de dos caras",
      "Escándalo diplomático en la Nueva York del siglo XIX",
    ],
    historical_context: {
      political_climate: "Estados Unidos intensificaba la persecución de la piratería y las relaciones diplomáticas con España eran delicadas.",
    },
    evidence_a_excerpt: "Juan García, un pirata notorio que operaba en aguas del Caribe, fue aprehendido ayer por las autoridades...",
    evidence_b_excerpt: "Don Juan García, hijo del embajador García de Madrid, ha sido detenido injustamente...",
  },
  de: {
    title: "Die zwei Juan García — Pirat oder Diplomat?",
    summary: "Im Jahr 1835 wurde ein Spanier namens 'Juan García' in New York verhaftet. Englische Zeitungen nannten ihn einen 'Piraten', aber die Aufzeichnungen des spanischen Konsulats identifizierten ihn als 'Sohn eines Diplomaten'. Wer war er wirklich?",
    narrative_content: "## Der Mann mit zwei Namen\n\nNew York, 1835. Inmitten des Trubels im Hafen wurde ein Spanier verhaftet. Juan García — sein Name erzählt zwei völlig verschiedene Geschichten.\n\nDie englischsprachige Zeitung 'New York Herald' berichtete von 'einem berüchtigten Piraten, der in der Karibik operiert'. Aber die offiziellen Aufzeichnungen des spanischen Konsulats besagen: 'Don Juan García, Sohn des Botschafters García aus Madrid'.\n\nPirat oder Diplomatensohn — oder vielleicht beides?",
    discrepancy_detected: "Die Identität des Verhafteten unterscheidet sich vollständig zwischen englischen Zeitungen und spanischen Diplomatendokumenten.",
    hypothesis: "Es könnte eine Person gleichen Namens gegeben haben, oder die Identität wurde aus diplomatischen Gründen absichtlich verschleiert.",
    alternative_hypotheses: [
      "Der Diplomatensohn war tatsächlich an Piraterie beteiligt",
      "Das spanische Konsulat versuchte eine Rettung durch Identitätsfälschung",
    ],
    story_hooks: [
      "Pirat oder Diplomat? — Der Mann mit zwei Gesichtern",
      "Diplomatischer Skandal im New York des 19. Jahrhunderts",
    ],
    historical_context: {
      political_climate: "Die USA verstärkten die Verfolgung der Piraterie und die diplomatischen Beziehungen zu Spanien waren heikel.",
    },
    evidence_a_excerpt: "Juan García, ein berüchtigter Pirat in karibischen Gewässern, wurde gestern von den Behörden festgenommen...",
    evidence_b_excerpt: "Don Juan García, Sohn des Botschafters García aus Madrid, wurde zu Unrecht inhaftiert...",
  },
  fr: {
    title: "Les deux Juan García — Pirate ou diplomate ?",
    summary: "En 1835, un Espagnol nommé 'Juan García' fut arrêté à New York. Les journaux anglais le qualifièrent de 'pirate', mais les registres du consulat espagnol l'identifièrent comme 'fils d'un diplomate'. Qui était-il vraiment ?",
    narrative_content: "## L'homme aux deux noms\n\nNew York, 1835. Au milieu de l'agitation du port, un Espagnol fut arrêté. Juan García — son nom raconte deux histoires complètement différentes.\n\nLe journal anglophone 'New York Herald' rapporta 'un pirate notoire opérant dans les Caraïbes'. Mais les registres officiels du consulat espagnol indiquent : 'Don Juan García, fils de l'ambassadeur García de Madrid'.\n\nPirate ou fils de diplomate — ou peut-être les deux ?",
    discrepancy_detected: "L'identité de l'arrêté diffère complètement entre les journaux anglais et les documents diplomatiques espagnols.",
    hypothesis: "Il pourrait y avoir eu une personne du même nom, ou l'identité a été délibérément dissimulée pour des raisons diplomatiques.",
    alternative_hypotheses: [
      "Le fils du diplomate était réellement impliqué dans la piraterie",
      "Le consulat espagnol a tenté le sauvetage en falsifiant l'identité",
    ],
    story_hooks: [
      "Pirate ou diplomate ? — L'homme aux deux visages",
      "Scandale diplomatique dans le New York du XIXe siècle",
    ],
    historical_context: {
      political_climate: "Les États-Unis intensifiaient la répression de la piraterie et les relations diplomatiques avec l'Espagne étaient délicates.",
    },
    evidence_a_excerpt: "Juan García, un pirate notoire opérant dans les eaux des Caraïbes, a été appréhendé hier par les autorités...",
    evidence_b_excerpt: "Don Juan García, fils de l'ambassadeur García de Madrid, a été injustement détenu...",
  },
  nl: {
    title: "De twee Juan García's — Piraat of diplomaat?",
    summary: "In 1835 werd een Spanjaard genaamd 'Juan García' gearresteerd in New York. Engelse kranten noemden hem een 'piraat', maar de archieven van het Spaanse consulaat identificeerden hem als 'zoon van een diplomaat'. Wie was hij werkelijk?",
    narrative_content: "## De man met twee namen\n\nNew York, 1835. Te midden van de drukte in de haven werd een Spanjaard gearresteerd. Juan García — zijn naam vertelt twee totaal verschillende verhalen.\n\nDe Engelstalige krant 'New York Herald' meldde 'een beruchte piraat die opereerde in het Caribisch gebied'. Maar de officiële archieven van het Spaanse consulaat vermelden: 'Don Juan García, zoon van ambassadeur García uit Madrid'.\n\nPiraat of diplomatenzoon — of misschien allebei?",
    discrepancy_detected: "De identiteit van de gearresteerde verschilt volledig tussen Engelse kranten en Spaanse diplomatieke documenten.",
    hypothesis: "Er kan een persoon met dezelfde naam zijn geweest, of de identiteit werd om diplomatieke redenen opzettelijk verborgen.",
    alternative_hypotheses: [
      "De diplomatenzoon was daadwerkelijk betrokken bij piraterij",
      "Het Spaanse consulaat probeerde een redding door identiteitsvervalsing",
    ],
    story_hooks: [
      "Piraat of diplomaat? — De man met twee gezichten",
      "Diplomatiek schandaal in het 19e-eeuwse New York",
    ],
    historical_context: {
      political_climate: "De VS versterkten de vervolging van piraterij en de diplomatieke betrekkingen met Spanje waren gevoelig.",
    },
    evidence_a_excerpt: "Juan García, een beruchte piraat in Caribische wateren, werd gisteren door de autoriteiten aangehouden...",
    evidence_b_excerpt: "Don Juan García, zoon van ambassadeur García uit Madrid, is onterecht vastgehouden...",
  },
  pt: {
    title: "Os dois Juan García — Pirata ou diplomata?",
    summary: "Em 1835, um espanhol chamado 'Juan García' foi preso em Nova York. Jornais ingleses o chamaram de 'pirata', mas os registros do consulado espanhol o identificaram como 'filho de um diplomata'. Quem ele realmente era?",
    narrative_content: "## O homem com dois nomes\n\nNova York, 1835. No meio da agitação do porto, um espanhol foi preso. Juan García — seu nome conta duas histórias completamente diferentes.\n\nO jornal em inglês 'New York Herald' relatou 'um pirata notório operando no Caribe'. Mas os registros oficiais do consulado espanhol dizem: 'Don Juan García, filho do embaixador García de Madrid'.\n\nPirata ou filho de diplomata — ou talvez ambos?",
    discrepancy_detected: "A identidade do preso difere completamente entre os jornais ingleses e os documentos diplomáticos espanhóis.",
    hypothesis: "Pode ter existido uma pessoa com o mesmo nome, ou a identidade foi deliberadamente ocultada por razões diplomáticas.",
    alternative_hypotheses: [
      "O filho do diplomata realmente esteve envolvido em pirataria",
      "O consulado espanhol tentou o resgate falsificando a identidade",
    ],
    story_hooks: [
      "Pirata ou diplomata? — O homem de duas faces",
      "Escândalo diplomático na Nova York do século XIX",
    ],
    historical_context: {
      political_climate: "Os EUA intensificavam a perseguição à pirataria e as relações diplomáticas com a Espanha eram delicadas.",
    },
    evidence_a_excerpt: "Juan García, um pirata notório operando nas águas do Caribe, foi apreendido ontem pelas autoridades...",
    evidence_b_excerpt: "Don Juan García, filho do embaixador García de Madrid, foi injustamente detido...",
  },
};

/**
 * サンプルミステリーデータ（英語ベース + translations map）
 */
const sampleMysteries = [
  {
    mystery_id: "HIS-MA-617-20260201120000",
    title: "The Vanishing Cargo of the Santa Maria — Spices or Silver?",
    summary: "In 1820, the Spanish ship Santa Maria arrived at Boston Harbor. English newspapers reported 'spices,' but Spanish diplomatic documents recorded '3,000 silver coins.' Where did the cargo go?",
    narrative_content: "## The Truth Lost in the Fog\n\nStanding at Boston Harbor, one cannot help but imagine that spring morning of 1820. The morning when the Spanish ship Santa Maria quietly entered port — the mystery surrounding its cargo remains unsolved after more than 200 years.\n\nThe English newspaper 'Boston Daily Advertiser' reported the next day in a matter-of-fact tone: 'a Spanish vessel arrived carrying spices from the Caribbean.' However, the diplomatic documents of the Spanish consulate contain an entirely different description — '3,000 silver coins for the consulate.'\n\nWhy do the records of the same ship, from the same voyage, diverge so dramatically?",
    discrepancy_detected: "English newspapers reported 'spice cargo,' but Spanish diplomatic documents clearly state '3,000 silver coins.' There is a significant contradiction in the cargo information for the same vessel.",
    discrepancy_type: "narrative_gap",
    evidence_a: {
      source_type: "newspaper",
      source_language: "en",
      source_title: "The Boston Daily Advertiser",
      source_date: "1820-03-15",
      source_url: "https://chroniclingamerica.loc.gov/example",
      relevant_excerpt: "The Spanish vessel Santa Maria arrived at Boston Harbor yesterday, carrying a cargo of spices from the Caribbean...",
      location_context: "Boston, Massachusetts",
    },
    evidence_b: {
      source_type: "newspaper",
      source_language: "es",
      source_title: "Despacho del Consulado de España en Boston",
      source_date: "1820-03-14",
      source_url: "https://catalog.archives.gov/example",
      relevant_excerpt: "El navío Santa María transporta 3,000 monedas de plata destinadas al consulado...",
      location_context: "Boston, Massachusetts",
    },
    additional_evidence: [],
    hypothesis: "The cargo contradiction may be a deliberate manipulation of information to conceal smuggling. Given the tensions in US-Spanish relations at the time, Spain likely tried to keep the silver transport secret.",
    alternative_hypotheses: [
      "A simple mistake by the newspaper reporter in identifying the cargo",
      "Possible confusion between two different vessels",
      "The Spanish documents may refer to a different ship",
    ],
    confidence_level: "medium",
    historical_context: {
      time_period: "Early 1820s (Eve of the Monroe Doctrine)",
      geographic_scope: ["Boston", "Caribbean", "Spain"],
      relevant_events: [
        "Spanish colonial independence movements",
        "US-Spain diplomatic negotiations",
        "Adams-Onís Treaty (1819)",
      ],
      key_figures: ["John Quincy Adams", "Spanish Consul in Boston"],
      political_climate: "It was the period of decline of the Spanish Empire, with independence movements active in Latin America. The US had just acquired Florida by exploiting Spanish weakness.",
    },
    research_questions: [
      "Are records of the Santa Maria's captain and crew preserved?",
      "Do Boston customs records from the same period mention this vessel?",
      "Do Spanish diplomatic documents contain a final record of the silver coins' disposition?",
    ],
    story_hooks: [
      "The mystery of the vanished silver coins",
      "Early 19th century smuggling networks",
      "Diplomatic documents telling a different truth from newspapers",
    ],
    analysis_timestamp: new Date().toISOString(),
    status: "published",
    translations: translationsForMystery001,
  },
  {
    mystery_id: "CRM-NY-212-20260201130000",
    title: "The Two Juan Garcías — Pirate or Diplomat?",
    summary: "In 1835, a Spaniard named 'Juan García' was arrested in New York. English newspapers called him a 'pirate,' but Spanish consulate records identified him as 'the son of a diplomat.' Who was he really?",
    narrative_content: "## The Man with Two Names\n\nNew York, 1835. Amid the bustle of the port, a Spaniard was arrested. Juan García — his name tells two entirely different stories.\n\nThe English newspaper 'New York Herald' reported 'a notorious pirate operating in Caribbean waters.' But the official records of the Spanish consulate state: 'Don Juan García, son of Ambassador García of Madrid.'\n\nPirate or diplomat's son — or perhaps both?",
    discrepancy_detected: "The identity of the arrested individual differs completely between English newspapers and Spanish diplomatic documents.",
    discrepancy_type: "person_missing",
    evidence_a: {
      source_type: "newspaper",
      source_language: "en",
      source_title: "New York Herald",
      source_date: "1835-07-22",
      source_url: "https://chroniclingamerica.loc.gov/example2",
      relevant_excerpt: "Juan Garcia, a notorious pirate operating in the Caribbean waters, was apprehended yesterday by authorities...",
      location_context: "New York City",
    },
    evidence_b: {
      source_type: "newspaper",
      source_language: "es",
      source_title: "Correspondencia del Consulado de España en Nueva York",
      source_date: "1835-07-23",
      source_url: "https://catalog.archives.gov/example2",
      relevant_excerpt: "Don Juan García, hijo del embajador García de Madrid, ha sido detenido injustamente...",
      location_context: "New York City",
    },
    additional_evidence: [],
    hypothesis: "There may have been two people with the same name, or the identity was deliberately concealed for diplomatic reasons.",
    alternative_hypotheses: [
      "The diplomat's son was actually involved in piracy",
      "The Spanish consulate attempted a rescue by fabricating an identity",
    ],
    confidence_level: "low",
    historical_context: {
      time_period: "1830s (Jacksonian Era)",
      geographic_scope: ["New York City", "Caribbean", "Madrid"],
      relevant_events: ["Intensified crackdown on piracy in the Caribbean"],
      key_figures: ["Juan Garcia", "Spanish Ambassador García"],
      political_climate: "The US was intensifying its crackdown on piracy, and diplomatic relations with Spain were delicate.",
    },
    research_questions: [
      "Are trial records for Juan García preserved?",
      "Can the family composition of Spanish Ambassador García be confirmed?",
    ],
    story_hooks: [
      "Pirate or diplomat — the man with two faces",
      "19th century New York diplomatic scandal",
    ],
    analysis_timestamp: new Date().toISOString(),
    status: "published",
    translations: translationsForMystery002,
  },
  {
    mystery_id: "FLK-MA-978-20260201140000",
    title: "The Bell Witch of Salem's Lost Quarter",
    summary: "A neighborhood in Salem that appears in tax records but on no maps. Multiple witnesses describe a spectral bell that tolls at midnight, yet the local church denies ever having a bell tower.",
    discrepancy_detected: "Tax records from 1692 list properties in 'Bellwick Quarter' of Salem, but no contemporary map shows this neighborhood. The church registry mentions bell repairs but the building never had a tower.",
    discrepancy_type: "location_conflict",
    evidence_a: {
      source_type: "loc_digital",
      source_language: "en",
      source_title: "Salem Town Records, 1692",
      source_date: "1692-10-15",
      source_url: "https://digitalcollections.loc.gov/example3",
      relevant_excerpt: "Taxes assessed on properties within the Bellwick Quarter: three houses, one storehouse, and the meeting house with its bell...",
      location_context: "Salem, Massachusetts",
    },
    evidence_b: {
      source_type: "internet_archive",
      source_language: "en",
      source_title: "Map of Salem Village and Town, 1692",
      source_date: "1692-01-01",
      source_url: "https://archive.org/details/salemmap1692",
      relevant_excerpt: "Complete survey of Salem Town boundaries... [no reference to Bellwick Quarter found in any mapped area]",
      location_context: "Salem, Massachusetts",
    },
    additional_evidence: [],
    hypothesis: "Bellwick Quarter may have been deliberately removed from maps during the Salem witch trials, as the neighborhood may have been associated with accused witches.",
    alternative_hypotheses: [
      "A clerical error created a fictional neighborhood in tax records",
      "Bellwick Quarter was a colloquial name never used in official cartography",
    ],
    confidence_level: "low",
    historical_context: {
      time_period: "Late 17th Century (Salem Witch Trials Era)",
      geographic_scope: ["Salem", "Massachusetts Bay Colony"],
      relevant_events: ["Salem Witch Trials (1692)"],
      key_figures: [],
      political_climate: "Salem was engulfed in mass hysteria over witchcraft accusations.",
    },
    research_questions: [
      "Are there other references to Bellwick Quarter in colonial records?",
      "Were any accused witches associated with this neighborhood?",
    ],
    story_hooks: [
      "The neighborhood that history erased",
      "A phantom bell in a town with no bell tower",
    ],
    analysis_timestamp: new Date().toISOString(),
    status: "pending",
  },
];

/**
 * サンプルデータを投入
 */
async function seedFirestore() {
  console.log("🌱 サンプルデータの投入を開始します...\n");

  const mysteriesCollection = db.collection("mysteries");

  for (const mystery of sampleMysteries) {
    const docRef = mysteriesCollection.doc(mystery.mystery_id);

    const mysteryWithTimestamps = {
      ...mystery,
      createdAt: Timestamp.now(),
      updatedAt: Timestamp.now(),
      publishedAt: mystery.status === "published" ? Timestamp.now() : null,
    };

    await docRef.set(mysteryWithTimestamps);

    const langCount = mystery.translations
      ? Object.keys(mystery.translations).length
      : 0;
    console.log(
      `  ✅ ${mystery.mystery_id}: ${mystery.title} [${mystery.status}] (翻訳: ${langCount}言語)`
    );
  }

  console.log(`\n🎉 ${sampleMysteries.length} 件のサンプルデータを投入しました`);
  console.log("\nステータス:");
  console.log(`  - pending: ${sampleMysteries.filter((m) => m.status === "pending").length} 件`);
  console.log(`  - published: ${sampleMysteries.filter((m) => m.status === "published").length} 件`);
  console.log("\n翻訳付き記事:");
  for (const m of sampleMysteries) {
    if (m.translations) {
      console.log(`  - ${m.mystery_id}: ${Object.keys(m.translations).join(", ")}`);
    }
  }
}

// 実行
seedFirestore()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("エラー:", error);
    process.exit(1);
  });
