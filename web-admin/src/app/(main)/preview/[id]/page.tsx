import { getMysteryById } from "@/lib/firestore/mysteries"
import { notFound } from "next/navigation"
import { PreviewContent } from "./preview-content"

// Dynamic rendering for preview (no caching)
export const dynamic = "force-dynamic"

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const mystery = await getMysteryById(id)

  if (!mystery) {
    return { title: "Mystery Not Found | Ghost in the Archive" }
  }

  return {
    title: `[Preview] ${mystery.title} | Ghost in the Archive`,
    description: mystery.summary,
  }
}

export default async function PreviewPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const mystery = await getMysteryById(id)

  if (!mystery) {
    notFound()
  }

  return <PreviewContent mystery={mystery} />
}
