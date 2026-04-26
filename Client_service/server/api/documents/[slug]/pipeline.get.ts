import { backendFetch, getBackendUser, mapPipelineEvent } from '../../../utils/backend'

export default defineEventHandler(async (event) => {
  const user = await getBackendUser(event)
  const orgId = getRouterParam(event, 'slug') || ''
  const documents = await backendFetch<any[]>(
    event,
    `/organizations/${orgId}/documents?acting_user_id=${encodeURIComponent(user.id)}&limit=100`
  )

  const eventGroups = await Promise.all(documents.slice(0, 5).map(async (document) => {
    try {
      const pipeline = await backendFetch<{ events: any[] }>(
        event,
        `/documents/${document.id}/pipeline?acting_user_id=${encodeURIComponent(user.id)}`
      )
      return pipeline.events
    } catch {
      return []
    }
  }))

  const pipeline = eventGroups.flat().map(mapPipelineEvent)

  return {
    pipeline: pipeline.length ? pipeline : [
      {
        id: 'empty-pipeline',
        name: 'Waiting for documents',
        description: 'Upload a document to start ingest, chunking, embedding and indexing.',
        owner: 'Server pipeline',
        status: 'queued'
      }
    ]
  }
})
