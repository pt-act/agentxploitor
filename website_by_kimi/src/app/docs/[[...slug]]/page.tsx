import { generateStaticParams, docMetadata, indexMetadata } from '../content'
import DocsClient from './DocsClient'

export { generateStaticParams }

export default async function DocsPage({ params }: { params: Promise<{ slug?: string[] }> }) {
  const { slug: slugArray } = await params
  const slug = slugArray?.[0] || ''
  const metadata = docMetadata[slug] || indexMetadata
  
  return <DocsClient slug={slug} title={metadata.title} description={metadata.description} />
}
