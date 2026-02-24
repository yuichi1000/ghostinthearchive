/**
 * 画像のみを含む <p> タグを AST レベルで除去する rehype プラグイン。
 *
 * react-markdown は Markdown の `![alt](url)` を `<p><img></p>` に変換するが、
 * カスタム img コンポーネントがブロックレベル要素（<figure><div>）を返す場合、
 * `<p><figure><div>` という不正な HTML ネストが生じてハイドレーションエラーになる。
 *
 * このプラグインは hast AST を走査し、画像のみを含む段落から <p> ラッパーを除去する。
 * 外部パッケージ（rehype-unwrap-images）不要のインライン実装。
 */

interface HastNode {
  type: string
  tagName?: string
  value?: string
  children?: HastNode[]
}

export function rehypeUnwrapImages() {
  return (tree: HastNode) => {
    function walk(node: HastNode) {
      if (!node.children) return
      // 新配列を構築して置換（splice によるインデックスずれを回避）
      const newChildren: HastNode[] = []
      for (const child of node.children) {
        if (child.type === "element" && child.tagName === "p") {
          // 空白テキストノードを除外し、意味のあるノードのみ抽出
          const meaningful = (child.children || []).filter(
            (c) => !(c.type === "text" && !c.value?.trim())
          )
          // 画像のみで構成された段落なら <p> を除去し、画像を直接展開
          if (
            meaningful.length >= 1 &&
            meaningful.every(
              (c) => c.type === "element" && c.tagName === "img"
            )
          ) {
            newChildren.push(...meaningful)
            continue
          }
        }
        newChildren.push(child)
        walk(child)
      }
      node.children = newChildren
    }
    walk(tree)
  }
}
