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
      for (let i = 0; i < node.children.length; i++) {
        const child = node.children[i]
        if (child.type === "element" && child.tagName === "p") {
          // 空白テキストノードを除外し、意味のあるノードのみ抽出
          const meaningful = (child.children || []).filter(
            (c) => !(c.type === "text" && !c.value?.trim())
          )
          if (
            meaningful.length === 1 &&
            meaningful[0].type === "element" &&
            meaningful[0].tagName === "img"
          ) {
            node.children[i] = meaningful[0]
          }
        }
        walk(child)
      }
    }
    walk(tree)
  }
}
