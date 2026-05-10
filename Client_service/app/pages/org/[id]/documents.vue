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
          <button
            class="document-tab-select"
            type="button"
            @pointerdown.prevent="selectOpenDocument(document)"
            @mousedown.prevent="selectOpenDocument(document)"
            @click="selectOpenDocument(document)"
          >
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
          <div class="document-analysis-actions">
            <span :class="statusClass(selectedDocument.status)">{{ selectedDocument.status }}</span>
            <button
              v-if="isAnalysisRunning(selectedDocument)"
              class="btn-secondary document-analysis-button"
              type="button"
              @click="handleStopAnalysis(selectedDocument)"
            >
              <Icon name="lucide:square" />
              <span>Dừng xử lý</span>
            </button>
            <button
              v-else
              class="btn-dark document-analysis-button"
              type="button"
              @click="handleStartAnalysis(selectedDocument)"
            >
              <Icon name="lucide:play" />
              <span>Bắt đầu phân tích</span>
            </button>
          </div>
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

        <section class="document-analysis-panel" aria-label="Document analysis progress">
          <p v-if="analysisActionError || error" class="document-analysis-error">
            {{ analysisActionError || error }}
          </p>
          <div class="document-analysis-summary">
            <div>
              <p class="section-kicker">Pipeline</p>
              <strong>{{ selectedDocument.analysis?.message || getAnalysisStateLabel(selectedDocument) }}</strong>
            </div>
            <span v-if="selectedDocument.analysis?.locked" class="status-badge status-warning">Đang khóa xử lý</span>
            <span v-else class="status-badge status-info">Có thể xử lý</span>
          </div>
          <div class="analysis-progress-grid">
            <div class="analysis-progress">
              <div class="analysis-progress-label">
                <span>Parse / Chunking Worker</span>
                <strong>{{ getAnalysisProgress(selectedDocument, 'parse') }}%</strong>
              </div>
              <div class="analysis-progress-track">
                <span :style="{ width: `${getAnalysisProgress(selectedDocument, 'parse')}%` }" />
              </div>
            </div>
            <div class="analysis-progress">
              <div class="analysis-progress-label">
                <span>Graph / Search RAG</span>
                <strong>{{ getAnalysisProgress(selectedDocument, 'graph') }}%</strong>
              </div>
              <div class="analysis-progress-track">
                <span :style="{ width: `${getAnalysisProgress(selectedDocument, 'graph')}%` }" />
              </div>
            </div>
          </div>
        </section>

        <article :class="['document-preview', selectedDocumentPreview?.kind === 'text' && 'text-preview-mode']">
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
          <div v-else-if="selectedDocumentPreview?.kind === 'text'" class="document-preview-text-shell">
            <pre class="document-preview-text">{{ selectedDocumentPreview.content }}</pre>
          </div>
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
          <input class="sr-only" multiple type="file" :accept="SUPPORTED_UPLOAD_ACCEPT" @change="handleFileInput" />
          <Icon :class="isDragging && 'active'" name="lucide:cloud-upload" />
          <strong>{{ text.documents.dropzoneTitle }}</strong>
          <span>Chỉ hỗ trợ PDF, DOCX, XLSX/CSV và TXT.</span>
        </label>

        <p v-if="uploadValidationError" class="upload-validation-error">
          {{ uploadValidationError }}
        </p>

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
import { useDocuments } from '@/composables/documents/useDocuments'
import { useOrganization } from '@/composables/organizations/useOrganization'
import { useAppLocale } from '@/composables/system/useAppLocale'
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
const {
  error,
  getDocuments,
  getOpenDocumentIds,
  getSelectedDocumentId,
  getPreview,
  loadDocuments,
  uploadDocument,
  startAnalysis,
  stopAnalysis,
  openDocument: openDocumentInStore,
  selectDocument: selectDocumentInStore,
  closeDocument: closeDocumentInStore,
  closeAllDocuments: closeAllDocumentsInStore
} = useDocuments()

const slug = computed(() => (route.params.slug ?? route.params.id) as string)
const organization = computed(() => getOrganizationBySlug(slug.value))
const documents = computed(() => getDocuments(slug.value))
const openDocumentIds = computed(() => getOpenDocumentIds(slug.value))
const selectedDocumentId = computed(() => getSelectedDocumentId(slug.value))

const expandedFolders = ref(new Set<string>())
const isUploadOpen = ref(false)
const isDragging = ref(false)
const pendingUploads = ref<File[]>([])
const uploadValidationError = ref<string | null>(null)
const analysisActionError = ref<string | null>(null)
let analysisPollTimer: ReturnType<typeof setInterval> | null = null

const SUPPORTED_UPLOAD_EXTENSIONS = new Set(['pdf', 'docx', 'xlsx', 'csv', 'txt'])
const SUPPORTED_UPLOAD_ACCEPT = '.pdf,.docx,.xlsx,.csv,.txt'

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

  return folderDefinitions.value.map((folder: { id: string, name: string }) => ({
    ...folder,
    documents: grouped.get(folder.id) ?? []
  }))
})

const openDocuments = computed(() =>
  openDocumentIds.value
    .map((id: string) => documents.value.find((document: KnowledgeDocument) => document.id === id))
    .filter((document): document is KnowledgeDocument => Boolean(document))
)

const selectedDocument = computed(() => documents.value.find((document: KnowledgeDocument) => document.id === selectedDocumentId.value) ?? null)
const selectedDocumentPreview = computed(() => (selectedDocument.value ? getPreview(slug.value, selectedDocument.value.id) : null))

const toggleFolder = (folderId: string) => {
  const next = new Set(expandedFolders.value)

  if (next.has(folderId)) {
    next.delete(folderId)
  } else {
    next.add(folderId)
  }

  expandedFolders.value = next
}

const openDocument = (document: KnowledgeDocument) => openDocumentInStore(slug.value, document)

const selectOpenDocument = (document: KnowledgeDocument) => {
  selectDocumentInStore(slug.value, document)
}

const closeDocument = (documentId: string) => {
  closeDocumentInStore(slug.value, documentId)
}

const closeAllDocuments = () => {
  closeAllDocumentsInStore(slug.value)
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

const isSupportedUploadFile = (file: File) => {
  const extension = file.name.split('.').pop()?.toLowerCase() || ''
  return SUPPORTED_UPLOAD_EXTENSIONS.has(extension)
}

const syncPendingFiles = (files: FileList | File[]) => {
  const nextFiles = Array.from(files)
  const supportedFiles = nextFiles.filter(isSupportedUploadFile)
  const rejectedCount = nextFiles.length - supportedFiles.length

  uploadValidationError.value = rejectedCount
    ? `Đã bỏ qua ${rejectedCount} file không hỗ trợ. Chỉ nhận PDF, DOCX, XLSX/CSV và TXT.`
    : null

  const byKey = new Map(pendingUploads.value.map((file: File) => [`${file.name}-${file.size}`, file] as const))

  for (const file of supportedFiles) {
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
  uploadValidationError.value = null
  isDragging.value = false
  isUploadOpen.value = false
}

const handleUpload = async () => {
  for (const file of pendingUploads.value) {
    await uploadDocument(slug.value, file)
  }

  clearUploadModal()
}

const handleStartAnalysis = async (document: KnowledgeDocument) => {
  analysisActionError.value = null

  try {
    await startAnalysis(slug.value, document.id)
  } catch (err) {
    analysisActionError.value = getActionErrorMessage(err, 'Không bắt đầu được phân tích tài liệu.')
  }
}

const handleStopAnalysis = async (document: KnowledgeDocument) => {
  analysisActionError.value = null

  try {
    await stopAnalysis(slug.value, document.id)
  } catch (err) {
    analysisActionError.value = getActionErrorMessage(err, 'Không dừng được phân tích tài liệu.')
  }
}

const getActionErrorMessage = (err: unknown, fallback: string) => {
  if (err && typeof err === 'object' && 'data' in err) {
    const data = (err as { data?: { detail?: string, message?: string, statusMessage?: string } }).data
    return data?.detail || data?.message || data?.statusMessage || fallback
  }

  return err instanceof Error ? err.message : fallback
}

const statusClass = (status: string) => {
  if (status === 'indexed') {
    return 'status-badge status-success'
  }

  if (status === 'embedded' || status === 'chunked' || status === 'processing' || status === 'indexing') {
    return 'status-badge status-info'
  }

  return 'status-badge status-warning'
}

const getAnalysisProgress = (document: KnowledgeDocument, key: 'parse' | 'graph') => {
  const rawValue = document.analysis?.progress?.[key]
  const numericValue = typeof rawValue === 'number' ? rawValue : 0

  return Math.max(0, Math.min(100, Math.round(numericValue)))
}

const isAnalysisRunning = (document: KnowledgeDocument) =>
  Boolean(document.analysis?.locked || document.status === 'processing' || document.status === 'indexing')

const getAnalysisStateLabel = (document: KnowledgeDocument) => {
  if (document.status === 'uploaded') {
    return 'Tài liệu đã upload, chưa chạy phân tích.'
  }

  if (document.status === 'indexed') {
    return 'Tài liệu đã sẵn sàng tìm kiếm.'
  }

  if (document.status === 'cancelled') {
    return 'Pipeline đã dừng.'
  }

  if (document.status === 'failed') {
    return document.analysis?.error || 'Pipeline xử lý thất bại.'
  }

  return document.analysis?.state || document.status
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
  getPreview(slug.value, document.id)?.url || ''

onMounted(async () => {
  await loadOrganizations()
  await loadDocuments(slug.value)

  expandedFolders.value = new Set(folderDefinitions.value.map((folder: DocumentFolder) => folder.id))

  analysisPollTimer = setInterval(() => {
    if (documents.value.some(isAnalysisRunning)) {
      void loadDocuments(slug.value)
    }
  }, 3000)
})

onBeforeUnmount(() => {
  if (analysisPollTimer) {
    clearInterval(analysisPollTimer)
    analysisPollTimer = null
  }
})

watch(selectedDocument, (document: KnowledgeDocument | null) => {
  if (document) {
    selectDocumentInStore(slug.value, document)
  }
})
</script>
