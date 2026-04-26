<template>
  <main v-if="organization" class="document-reader-page">
    <aside class="document-explorer">
      <div class="document-explorer-toolbar">
        <h1>{{ text.documents.treeTitle }}</h1>
        <button class="document-upload-trigger" type="button" @click="isUploadOpen = true">
          <Icon name="lucide:upload" />
          <span>{{ text.documents.upload }}</span>
        </button>
      </div>

      <div class="document-tree">
        <div v-for="folder in documentTree" :key="folder.id" class="document-folder">
          <button
            class="document-tree-item"
            type="button"
            :aria-expanded="expandedFolders.has(folder.id)"
            @click="toggleFolder(folder.id)"
          >
            <Icon :name="expandedFolders.has(folder.id) ? 'lucide:folder-open' : 'lucide:folder'" />
            <span>{{ folder.name }}</span>
            <Icon class="document-tree-chevron" :name="expandedFolders.has(folder.id) ? 'lucide:chevron-down' : 'lucide:chevron-right'" />
          </button>

          <div v-if="expandedFolders.has(folder.id)" class="document-folder-children">
            <button
              v-for="document in folder.documents"
              :key="document.id"
              :class="['document-tree-item file', selectedDocumentId === document.id && 'active']"
              type="button"
              @click="openDocument(document)"
            >
              <Icon :name="getDocumentIcon(document.title)" />
              <span>{{ document.title }}</span>
            </button>

            <p v-if="!folder.documents.length" class="document-empty-tree">
              {{ text.documents.emptyFolder }}
            </p>
          </div>
        </div>
      </div>
    </aside>

    <section class="document-viewer">
      <div v-if="openDocuments.length" class="document-tabs">
        <div
          v-for="document in openDocuments"
          :key="document.id"
          :class="['document-tab', selectedDocumentId === document.id && 'active']"
        >
          <button class="document-tab-select" type="button" @click="selectedDocumentId = document.id">
            <Icon :name="getDocumentIcon(document.title)" />
            <span>{{ document.title }}</span>
          </button>
          <button class="document-tab-close" type="button" @click.stop="closeDocument(document.id)">
            <Icon name="lucide:x" />
          </button>
        </div>

        <button class="document-tabs-close-all" type="button" @click="closeAllDocuments">
          {{ text.documents.closeAll }}
        </button>
      </div>

      <div v-if="selectedDocument" class="document-content">
        <div class="document-content-header">
          <div class="min-w-0">
            <p class="section-kicker">{{ selectedDocument.status }}</p>
            <h2>{{ selectedDocument.title }}</h2>
          </div>
          <span :class="statusClass(selectedDocument.status)">{{ selectedDocument.status }}</span>
        </div>

        <div class="document-meta-grid">
          <div>
            <span>{{ text.documents.chunkColumn }}</span>
            <strong>{{ selectedDocument.chunkCount }}</strong>
          </div>
          <div>
            <span>{{ text.documents.embeddingColumn }}</span>
            <strong>{{ selectedDocument.embeddingModel }}</strong>
          </div>
          <div>
            <span>{{ text.documents.sourceColumn }}</span>
            <strong>{{ selectedDocument.sourceStorage }}</strong>
          </div>
          <div>
            <span>{{ text.documents.uploadedBy }}</span>
            <strong>{{ selectedDocument.uploadedBy }}</strong>
          </div>
        </div>

        <article class="document-preview">
          <p>{{ text.documents.previewLead }}</p>
          <iframe
            v-if="isPdfDocument(selectedDocument)"
            :src="getDocumentContentUrl(selectedDocument)"
            class="document-preview-frame"
            :title="selectedDocument.title"
          />
          <img
            v-else-if="isImageDocument(selectedDocument)"
            :src="getDocumentContentUrl(selectedDocument)"
            :alt="selectedDocument.title"
            class="document-preview-image"
          />
          <pre v-else-if="selectedDocumentPreview?.kind === 'text'" class="document-preview-text">{{ selectedDocumentPreview.content }}</pre>
          <p v-else-if="selectedDocumentPreview?.message">{{ selectedDocumentPreview.message }}</p>
          <p v-else>{{ getDocumentPreview(selectedDocument) }}</p>
        </article>
      </div>

      <div v-else class="document-empty-viewer">
        <Icon name="lucide:file-search" />
        <h2>{{ text.documents.emptyViewerTitle }}</h2>
        <p>{{ text.documents.emptyViewerDescription }}</p>
      </div>
    </section>

    <AppPopup
      v-model:open="isUploadOpen"
      teleport
      root-class="contents"
      backdrop-class="modal-backdrop"
      content-class="modal-shell"
      transition-name="zoom"
      :close-on-outside="false"
      :close-on-backdrop="false"
    >
      <div class="upload-modal-card">
        <header class="modal-header">
          <div>
            <p class="section-kicker">{{ text.documents.uploadEyebrow }}</p>
            <h2 class="panel-title">{{ text.documents.uploadTitle }}</h2>
          </div>
          <button class="icon-action-light" type="button" @click="isUploadOpen = false">
            <Icon name="lucide:x" />
          </button>
        </header>

        <label
          class="upload-dropzone"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input class="sr-only" multiple type="file" @change="handleFileInput" />
          <Icon :class="isDragging && 'active'" name="lucide:cloud-upload" />
          <strong>{{ text.documents.dropzoneTitle }}</strong>
          <span>{{ text.documents.dropzoneDescription }}</span>
        </label>

        <div v-if="pendingUploads.length" class="upload-file-list">
          <div v-for="file in pendingUploads" :key="`${file.name}-${file.size}`" class="upload-file-row">
            <Icon :name="getDocumentIcon(file.name)" />
            <span>{{ file.name }}</span>
          </div>
        </div>

        <footer class="modal-footer">
          <button class="btn-secondary" type="button" @click="clearUploadModal">{{ text.common.cancel }}</button>
          <button class="btn-primary" type="button" :disabled="!pendingUploads.length" @click="handleUpload">
            {{ text.documents.upload }}
          </button>
        </footer>
      </div>
    </AppPopup>
  </main>
</template>

<script setup lang="ts">
import type { KnowledgeDocument } from '@/types/organization'
import { DOCUMENT_FOLDER_IDS, DOCUMENT_FOLDER_KEYWORDS } from '@/constants/documents'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

interface DocumentFolder {
  id: string
  name: string
  documents: KnowledgeDocument[]
}

const { text } = useAppLocale()

const route = useRoute()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()
const { getDocuments, loadDocuments, uploadDocument } = useDocuments()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const documents = computed(() => getDocuments(slug.value))

const expandedFolders = ref(new Set<string>())
const openDocumentIds = ref<string[]>([])
const selectedDocumentId = ref<string | null>(null)
const isUploadOpen = ref(false)
const isDragging = ref(false)
const pendingUploads = ref<File[]>([])
const previewsByDocumentId = ref<Record<string, { kind: string, content?: string | null, message?: string | null }>>({})

const folderDefinitions = computed(() => [
  { id: DOCUMENT_FOLDER_IDS.people, name: text.documents.peopleFolder },
  { id: DOCUMENT_FOLDER_IDS.operations, name: text.documents.operationsFolder },
  { id: DOCUMENT_FOLDER_IDS.finance, name: text.documents.financeFolder },
  { id: DOCUMENT_FOLDER_IDS.faq, name: text.documents.faqFolder }
])

const getDocumentFolderId = (document: KnowledgeDocument) => {
  const title = document.title.toLowerCase()

  if (DOCUMENT_FOLDER_KEYWORDS.people.some((keyword) => title.includes(keyword))) {
    return DOCUMENT_FOLDER_IDS.people
  }

  if (DOCUMENT_FOLDER_KEYWORDS.operations.some((keyword) => title.includes(keyword))) {
    return DOCUMENT_FOLDER_IDS.operations
  }

  if (DOCUMENT_FOLDER_KEYWORDS.finance.some((keyword) => title.includes(keyword))) {
    return DOCUMENT_FOLDER_IDS.finance
  }

  return DOCUMENT_FOLDER_IDS.faq
}

const documentTree = computed<DocumentFolder[]>(() => {
  const grouped = new Map<string, KnowledgeDocument[]>()

  for (const folder of folderDefinitions.value) {
    grouped.set(folder.id, [])
  }

  for (const document of documents.value) {
    const folderId = getDocumentFolderId(document)
    grouped.set(folderId, [...(grouped.get(folderId) ?? []), document])
  }

  return folderDefinitions.value.map((folder) => ({
    ...folder,
    documents: grouped.get(folder.id) ?? []
  }))
})

const openDocuments = computed(() =>
  openDocumentIds.value
    .map((id) => documents.value.find((document) => document.id === id))
    .filter((document): document is KnowledgeDocument => Boolean(document))
)

const selectedDocument = computed(() => documents.value.find((document) => document.id === selectedDocumentId.value) ?? null)
const selectedDocumentPreview = computed(() => {
  if (!selectedDocument.value) {
    return null
  }
  return previewsByDocumentId.value[selectedDocument.value.id] ?? null
})

const toggleFolder = (folderId: string) => {
  const next = new Set(expandedFolders.value)

  if (next.has(folderId)) {
    next.delete(folderId)
  } else {
    next.add(folderId)
  }

  expandedFolders.value = next
}

const openDocument = (document: KnowledgeDocument) => {
  if (!openDocumentIds.value.includes(document.id)) {
    openDocumentIds.value = [...openDocumentIds.value, document.id]
  }

  selectedDocumentId.value = document.id
}

const closeDocument = (documentId: string) => {
  const currentIndex = openDocumentIds.value.indexOf(documentId)
  openDocumentIds.value = openDocumentIds.value.filter((id) => id !== documentId)

  if (selectedDocumentId.value !== documentId) {
    return
  }

  selectedDocumentId.value = openDocumentIds.value[Math.max(0, currentIndex - 1)] ?? openDocumentIds.value[0] ?? null
}

const closeAllDocuments = () => {
  openDocumentIds.value = []
  selectedDocumentId.value = null
}

const getDocumentIcon = (title: string) => {
  const extension = title.split('.').pop()?.toLowerCase()

  if (extension === 'pdf') {
    return 'lucide:file-text'
  }

  if (extension === 'md' || extension === 'txt') {
    return 'lucide:file-type'
  }

  return 'lucide:file'
}

const syncPendingFiles = (files: FileList | File[]) => {
  const nextFiles = Array.from(files)
  const byKey = new Map(pendingUploads.value.map((file) => [`${file.name}-${file.size}`, file]))

  for (const file of nextFiles) {
    byKey.set(`${file.name}-${file.size}`, file)
  }

  pendingUploads.value = [...byKey.values()]
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false

  if (event.dataTransfer?.files.length) {
    syncPendingFiles(event.dataTransfer.files)
  }
}

const handleFileInput = (event: Event) => {
  const target = event.target as HTMLInputElement

  if (target.files?.length) {
    syncPendingFiles(target.files)
  }

  target.value = ''
}

const clearUploadModal = () => {
  pendingUploads.value = []
  isDragging.value = false
  isUploadOpen.value = false
}

const handleUpload = async () => {
  for (const file of pendingUploads.value) {
    await uploadDocument(slug.value, file)
  }

  clearUploadModal()
}

const statusClass = (status: string) => {
  if (status === 'indexed') {
    return 'status-badge status-success'
  }

  if (status === 'embedded' || status === 'chunked') {
    return 'status-badge status-info'
  }

  return 'status-badge status-warning'
}

const getDocumentPreview = (document: KnowledgeDocument) =>
  text.documents.previewTemplate
    .replace('{title}', document.title)
    .replace('{storage}', document.sourceStorage)
    .replace('{uploadedAt}', document.uploadedAt)

const isPdfDocument = (document: KnowledgeDocument) => document.title.toLowerCase().endsWith('.pdf')
const isImageDocument = (document: KnowledgeDocument) =>
  ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'].some((extension) => document.title.toLowerCase().endsWith(extension))

const getDocumentContentUrl = (document: KnowledgeDocument) =>
  `/api/documents/${encodeURIComponent(slug.value)}/${encodeURIComponent(document.id)}/content`

const loadDocumentPreview = async (document: KnowledgeDocument) => {
  if (isPdfDocument(document) || isImageDocument(document) || previewsByDocumentId.value[document.id]) {
    return
  }

  const preview = await $fetch<{ kind: string, content?: string | null, message?: string | null }>(
    `/api/documents/${encodeURIComponent(slug.value)}/${encodeURIComponent(document.id)}/preview`
  )

  previewsByDocumentId.value = {
    ...previewsByDocumentId.value,
    [document.id]: preview
  }
}

onMounted(async () => {
  await loadOrganizations()
  await loadDocuments(slug.value)

  expandedFolders.value = new Set(folderDefinitions.value.map((folder) => folder.id))
})

watch(selectedDocument, (document) => {
  if (document) {
    loadDocumentPreview(document)
  }
})
</script>
