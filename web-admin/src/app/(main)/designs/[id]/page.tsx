import { DesignDetail } from "./design-detail"

interface DesignDetailPageProps {
  params: Promise<{ id: string }>
}

export default async function DesignDetailPage({ params }: DesignDetailPageProps) {
  const { id } = await params
  return <DesignDetail designId={id} />
}
