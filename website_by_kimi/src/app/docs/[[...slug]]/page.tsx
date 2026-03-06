import { generateStaticParams, docMetadata, indexMetadata } from '../content'
import DocsClient from './DocsClient'

export { generateStaticParams }

export default function DocsPage({ params }: { params: { slug?: string[] } }) {
  const slug = params?.slug?.[0] || ''
  const metadata = docMetadata[slug] || indexMetadata
  
  return <DocsClient slug={slug} title={metadata.title} description={metadata.description} />
}
