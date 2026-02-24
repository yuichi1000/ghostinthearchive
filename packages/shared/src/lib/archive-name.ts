import type { Evidence } from "../types/mystery";

/**
 * URL ドメインパターン → アーカイブ表示名マッピング
 * ドメインの部分一致で判定（source_url に含まれるか）
 */
const URL_DOMAIN_MAP: [string, string][] = [
  // loc.gov は LOC Digital Collections と Chronicling America の両方を含む
  ["loc.gov", "Library of Congress"],
  ["dp.la", "DPLA"],
  ["nypl.org", "NYPL Digital Collections"],
  ["archive.org", "Internet Archive"],
  ["europeana.eu", "Europeana"],
  ["deutsche-digitale-bibliothek.de", "Deutsche Digitale Bibliothek"],
  ["delpher.nl", "Delpher"],
  ["kb.nl", "Delpher"],
  ["wellcomecollection.org", "Wellcome Collection"],
  ["nla.gov.au", "Trove"],
  ["natlib.govt.nz", "DigitalNZ"],
  ["digitalnz.org", "DigitalNZ"],
  ["paperspast.natlib.govt.nz", "DigitalNZ"],
  ["ndlsearch.ndl.go.jp", "National Diet Library"],
  ["dl.ndl.go.jp", "National Diet Library"],
];

/**
 * source_type → アーカイブ表示名フォールバック
 */
const SOURCE_TYPE_MAP: Record<string, string> = {
  newspaper: "Library of Congress",
  loc_digital: "Library of Congress",
  dpla: "DPLA",
  nypl: "NYPL Digital Collections",
  internet_archive: "Internet Archive",
  europeana: "Europeana",
  ddb: "Deutsche Digitale Bibliothek",
  delpher: "Delpher",
  wellcome: "Wellcome Collection",
  trove: "Trove",
  digitalnz: "DigitalNZ",
  ndl: "National Diet Library",
};

/**
 * 証拠データからデジタルアーカイブ名を導出する
 *
 * 1. source_url のドメインパターンマッチ（主）
 * 2. source_type からのフォールバック（副）
 * 3. いずれも不明なら undefined
 */
export function getArchiveName(evidence: Evidence): string | undefined {
  // URL パターンマッチ
  if (evidence.source_url) {
    for (const [domain, name] of URL_DOMAIN_MAP) {
      if (evidence.source_url.includes(domain)) {
        return name;
      }
    }
  }

  // source_type フォールバック
  if (evidence.source_type) {
    return SOURCE_TYPE_MAP[evidence.source_type];
  }

  return undefined;
}
