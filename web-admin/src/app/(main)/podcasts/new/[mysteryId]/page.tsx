import { NewPodcastForm } from "./new-podcast-form"

interface NewPodcastPageProps {
  params: Promise<{ mysteryId: string }>
}

export default async function NewPodcastPage({ params }: NewPodcastPageProps) {
  const { mysteryId } = await params
  return <NewPodcastForm mysteryId={mysteryId} />
}
