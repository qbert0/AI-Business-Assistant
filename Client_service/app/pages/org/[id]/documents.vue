<template>
  <div v-if="organization" class="org-content-page">
    <section class="surface-card org-hero-card space-y-4">
      <div class="section-heading">
        <div>
          <p class="eyebrow">{{ text.documents.eyebrow }}</p>
          <h1 class="page-title">{{ organization.name }}</h1>
          <p class="muted-copy">{{ text.documents.description }}</p>
        </div>

        <div class="flex flex-wrap gap-2">
          <button class="btn-secondary" type="button" @click="promptCreateFolder(null)">{{ text.documents.addFolder }}</button>
          <button class="btn-primary" type="button" @click="openUploadModal(null)">{{ text.documents.addFile }}</button>
        </div>
      </div>
    </section>

    <section class="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
      <article class="surface-card space-y-4">
        <div class="section-heading">
          <h2 class="panel-title">{{ text.documents.treeTitle }}</h2>
          <span class="text-caption text-olive">{{ treeNodeCount }}</span>
        </div>

        <div class="space-y-2">
          <DocumentTreeNode
            v-for="node in documentTree"
            :key="node.id"
            :node="node"
            :depth="0"
            :selected-document-id="selectedDocumentId"
            :expanded-ids="expandedIds"
            @toggle="toggleFolder"
            @open-file="openDocumentNode"
            @add-folder="promptCreateFolder"
            @add-file="openUploadModal"
            @rename="renameNode"
          />

          <p v-if="!documentTree.length" class="rounded-2xl border border-dashed border-cream bg-white px-4 py-5 text-sm text-olive">
            {{ text.documents.emptyTree }}
          </p>
        </div>
      </article>

      <section class="surface-card space-y-4">
        <div v-if="openDocuments.length" class="document-tabs">
          <div
            v-for="document in openDocuments"
            :key="document.id"
            :class="['document-tab', selectedDocumentId === document.id && 'active']"
          >
            <button class="document-tab-select" type="button" @click="selectDocumentInStore(slug, document)">
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

        <div v-if="selectedDocument" class="space-y-4">
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
          <button class="icon-action-light" type="button" @click="clearUploadModal">
            <Icon name="lucide:x" />
          </button>
        </header>

        <label
          v-if="!pendingUploads.length"
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
          <button v-if="pendingUploads.length" class="btn-secondary" type="button" @click="pendingUploads = []">{{ text.documents.changeFiles }}</button>
          <button class="btn-secondary" type="button" @click="clearUploadModal">{{ text.common.cancel }}</button>
          <button class="btn-primary" type="button" :disabled="!pendingUploads.length || isSavingTree" @click="handleUpload">
            {{ text.documents.upload }}
          </button>
        </footer>
      </div>
    </AppPopup>
  </div>
</template>

<script setup lang="ts">
import DocumentTreeNode from '@/components/documents/DocumentTreeNode.vue'
import type { KnowledgeDocument, OrganizationDocumentTreeNode } from '@/types/organization'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()

const route = useRoute()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()
const settingsApi = useApiOrganizationSettings()
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

const slug = computed(() => String(route.params.slug ?? route.params.id ?? ''))
const organization = computed(() => getOrganizationBySlug(slug.value))
const documents = computed(() => getDocuments(slug.value))
const documentsById = computed(() => new Map(documents.value.map((item) => [item.id, item] as const)))
const openDocumentIds = computed(() => getOpenDocumentIds(slug.value))
const selectedDocumentId = computed(() => getSelectedDocumentId(slug.value))
const selectedDocument = computed(() => documents.value.find((document) => document.id === selectedDocumentId.value) ?? null)
const selectedDocumentPreview = computed(() => (selectedDocument.value ? getPreview(slug.value, selectedDocument.value.id) : null))

const treeState = ref<OrganizationDocumentTreeNode[]>([])
const expandedFolders = ref(new Set<string>())
const isUploadOpen = ref(false)
const isDragging = ref(false)
const pendingUploads = ref<File[]>([])
const uploadParentId = ref<string | null>(null)
const uploadValidationError = ref<string | null>(null)
const analysisActionError = ref<string | null>(null)
const isSavingTree = ref(false)
let analysisPollTimer: ReturnType<typeof setInterval> | null = null

const SUPPORTED_UPLOAD_EXTENSIONS = new Set(['pdf', 'docx', 'xlsx', 'csv', 'txt'])
const SUPPORTED_UPLOAD_ACCEPT = '.pdf,.docx,.xlsx,.csv,.txt'

const normalizeNode = (node: OrganizationDocumentTreeNode, parentId: string | null = null): OrganizationDocumentTreeNode => ({
  id: node.id,
  type: node.type,
  name: node.name,
  parentId,
  documentId: node.documentId ?? null,
  children: node.type === 'folder' ? (node.children ?? []).map((child) => normalizeNode(child, node.id)) : undefined
})

const cloneTree = (nodes: OrganizationDocumentTreeNode[]) => nodes.map((node) => normalizeNode(node, node.parentId ?? null))

const buildFallbackTree = () =>
  documents.value.map<OrganizationDocumentTreeNode>((document) => ({
    id: `document-${document.id}`,
    type: 'file',
    name: document.title,
    parentId: null,
    documentId: document.id
  }))

const documentTree = computed(() => (treeState.value.length ? treeState.value : buildFallbackTree()))
const expandedIds = computed(() => [...expandedFolders.value])
const treeNodeCount = computed(() => {
  const walk = (nodes: OrganizationDocumentTreeNode[]): number =>
    nodes.reduce((count, node) => count + 1 + (node.children ? walk(node.children) : 0), 0)
  return walk(documentTree.value)
})

const openDocuments = computed(() =>
  openDocumentIds.value
    .map((id) => documents.value.find((document) => document.id === id))
    .filter((document): document is KnowledgeDocument => Boolean(document))
)

const persistTree = async (nextTree: OrganizationDocumentTreeNode[]) => {
  isSavingTree.value = true
  try {
    treeState.value = cloneTree(nextTree)
    await settingsApi.update(slug.value, {
      settings: {
        documentTree: treeState.value
      }
    })
  } finally {
    isSavingTree.value = false
  }
}

const loadTree = async () => {
  const response = await settingsApi.get(slug.value)
  treeState.value = Array.isArray(response.settings.documentTree)
    ? response.settings.documentTree.map((node) => normalizeNode(node))
    : []

  const seedFolders = new Set<string>()
  const collectFolders = (nodes: OrganizationDocumentTreeNode[]) => {
    for (const node of nodes) {
      if (node.type === 'folder') {
        seedFolders.add(node.id)
        collectFolders(node.children ?? [])
      }
    }
  }

  collectFolders(treeState.value)
  expandedFolders.value = seedFolders
}

const withTreeMutation = (
  nodes: OrganizationDocumentTreeNode[],
  targetId: string,
  updater: (node: OrganizationDocumentTreeNode) => OrganizationDocumentTreeNode
): OrganizationDocumentTreeNode[] =>
  nodes.map((node) => {
    if (node.id === targetId) {
      return updater(node)
    }

    if (node.children?.length) {
      return {
        ...node,
        children: withTreeMutation(node.children, targetId, updater)
      }
    }

    return node
  })

const appendNode = (nodes: OrganizationDocumentTreeNode[], parentId: string | null, nextNode: OrganizationDocumentTreeNode) => {
  if (!parentId) {
    return [...nodes, nextNode]
  }

  return withTreeMutation(nodes, parentId, (node) => ({
    ...node,
    children: [...(node.children ?? []), nextNode]
  }))
}

const findNode = (nodes: OrganizationDocumentTreeNode[], targetId: string): OrganizationDocumentTreeNode | null => {
  for (const node of nodes) {
    if (node.id === targetId) {
      return node
    }
    if (node.children?.length) {
      const found = findNode(node.children, targetId)
      if (found) {
        return found
      }
    }
  }
  return null
}

const promptCreateFolder = async (parentId: string | null) => {
  const name = window.prompt(text.documents.folderPrompt)
  if (!name?.trim()) {
    return
  }

  const nextNode: OrganizationDocumentTreeNode = {
    id: `folder-${Date.now()}`,
    type: 'folder',
    name: name.trim(),
    parentId,
    children: []
  }

  expandedFolders.value = new Set([...expandedFolders.value, nextNode.id, ...(parentId ? [parentId] : [])])
  await persistTree(appendNode(documentTree.value, parentId, nextNode))
}

const renameNode = async (nodeId: string) => {
  const currentNode = findNode(documentTree.value, nodeId)
  if (!currentNode) {
    return
  }

  const name = window.prompt(text.documents.renamePrompt, currentNode.name)
  if (!name?.trim()) {
    return
  }

  await persistTree(withTreeMutation(documentTree.value, nodeId, (node) => ({ ...node, name: name.trim() })))
}

const toggleFolder = (folderId: string) => {
  const next = new Set(expandedFolders.value)
  if (next.has(folderId)) {
    next.delete(folderId)
  } else {
    next.add(folderId)
  }
  expandedFolders.value = next
}

const openDocumentNode = async (node: OrganizationDocumentTreeNode) => {
  if (!node.documentId) {
    return
  }

  const document = documentsById.value.get(node.documentId)
  if (document) {
    await openDocumentInStore(slug.value, document)
  }
}

const openUploadModal = (parentId: string | null) => {
  uploadParentId.value = parentId
  uploadValidationError.value = null
  isUploadOpen.value = true
}

const closeDocument = (documentId: string) => closeDocumentInStore(slug.value, documentId)
const closeAllDocuments = () => closeAllDocumentsInStore(slug.value)

const getDocumentIcon = (title: string) => {
  const extension = title.split('.').pop()?.toLowerCase()
  if (extension === 'pdf') return 'lucide:file-text'
  if (extension === 'md' || extension === 'txt' || extension === 'docx') return 'lucide:file-type'
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(extension || '')) return 'lucide:image'
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

  const byKey = new Map(pendingUploads.value.map((file) => [`${file.name}-${file.size}`, file] as const))
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
  uploadParentId.value = null
  uploadValidationError.value = null
  isDragging.value = false
  isUploadOpen.value = false
}

const handleUpload = async () => {
  const hadPersistedTree = treeState.value.length > 0

  for (const file of pendingUploads.value) {
    await uploadDocument(slug.value, file)
  }

  await loadDocuments(slug.value)

  if (!hadPersistedTree && !uploadParentId.value) {
    await persistTree(buildFallbackTree())
    clearUploadModal()
    return
  }

  let nextTree = documentTree.value
  for (const file of pendingUploads.value) {
    const matched = documents.value.find((document) => document.title === file.name)
    if (!matched) {
      continue
    }

    nextTree = appendNode(nextTree, uploadParentId.value, {
      id: `document-${matched.id}`,
      type: 'file',
      name: matched.title,
      parentId: uploadParentId.value,
      documentId: matched.id
    })
  }

  await persistTree(nextTree)
  clearUploadModal()
}

const getActionErrorMessage = (err: unknown, fallback: string) => {
  if (err && typeof err === 'object' && 'data' in err) {
    const data = (err as { data?: { detail?: string, message?: string, statusMessage?: string } }).data
    return data?.detail || data?.message || data?.statusMessage || fallback
  }

  return err instanceof Error ? err.message : fallback
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

const getDocumentContentUrl = (document: KnowledgeDocument) => getPreview(slug.value, document.id)?.url || ''

onMounted(async () => {
  await loadOrganizations()
  await loadDocuments(slug.value)
  await loadTree()

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
</script>
