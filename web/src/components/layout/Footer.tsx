import { ExternalLink } from "lucide-react";

/**
 * Footer コンポーネント
 * サイト共通のフッター
 */
export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-paper mt-auto">
      <div className="container-wide py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* プロジェクト情報 */}
          <div>
            <h3 className="font-serif text-lg font-semibold mb-3">
              Ghost in the Archive
            </h3>
            <p className="text-sm text-muted leading-relaxed">
              公開情報から歴史的ミステリーを発掘し、
              物語として再構成するAIシステム。
              歴史の影に隠された真実を探ります。
            </p>
          </div>

          {/* データソース */}
          <div>
            <h4 className="font-medium text-sm mb-3 uppercase tracking-wide text-muted">
              データソース
            </h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="https://www.loc.gov/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted hover:text-navy inline-flex items-center gap-1"
                >
                  Library of Congress
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.archives.gov/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted hover:text-navy inline-flex items-center gap-1"
                >
                  National Archives (NARA)
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              </li>
              <li>
                <a
                  href="https://chroniclingamerica.loc.gov/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted hover:text-navy inline-flex items-center gap-1"
                >
                  Chronicling America
                  <ExternalLink className="h-3 w-3" aria-hidden="true" />
                </a>
              </li>
            </ul>
          </div>

          {/* 技術情報 */}
          <div>
            <h4 className="font-medium text-sm mb-3 uppercase tracking-wide text-muted">
              技術スタック
            </h4>
            <ul className="space-y-2 text-sm text-muted">
              <li>Agent Development Kit (ADK)</li>
              <li>Gemini Pro / Flash</li>
              <li>Next.js 16</li>
              <li>Cloud Firestore</li>
            </ul>
          </div>
        </div>

        {/* コピーライト */}
        <div className="mt-8 pt-6 border-t border-border text-center">
          <p className="text-xs text-muted">
            &copy; {currentYear} Ghost in the Archive.
            歴史的資料は各公文書館の利用規約に従います。
          </p>
        </div>
      </div>
    </footer>
  );
}
