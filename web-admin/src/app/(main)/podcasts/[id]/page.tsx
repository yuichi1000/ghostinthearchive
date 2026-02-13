import { PodcastDetail } from "./podcast-detail"

interface PodcastDetailPageProps {
  params: Promise<{ id: string }>
}

export default async function PodcastDetailPage({ params }: PodcastDetailPageProps) {
  const { id } = await params
  return <PodcastDetail podcastId={id} />
}
