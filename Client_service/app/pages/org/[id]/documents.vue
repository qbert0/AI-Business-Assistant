<template>
  <div v-if="organization" class="org-content-page">
    <section v-if="remediationQuestion || remediationResultMessage" class="surface-card upload-remediation-banner">
      <div>
        <p class="section-kicker">Khắc phục phản hồi</p>
        <h2>{{ remediationQuestion || 'Kiểm tra lại câu hỏi đã bị phản hồi' }}</h2>
        <p v-if="remediationResultMessage" class="table-copy">{{ remediationResultMessage }}</p>
        <p v-else-if="isRemediationChecking" class="table-copy">
          <Icon name="lucide:loader-circle" class="upload-spinner" />
          Đang kiểm tra tài liệu khắc phục trong nền.
        </p>
      </div>
      <button v-if="!isPublicReadOnly" class="btn-primary" type="button" @click="openUploadModal(null)">
        <Icon name="lucide:upload" />
        Tải tài liệu khắc phục
      </button>
    </section>

    <section class="document-flex-layout" :style="{ '--document-tree-width': `${treePanelWidth}px` }">
      <article class="surface-card document-tree-panel">
        <div class="section-heading">
          <h2 class="document-tree-heading">{{ text.documents.treeTitle }}</h2>
          <div class="flex flex-wrap items-center justify-end gap-2">
            <span class="text-caption text-olive">{{ treeNodeCount }}</span>
            <button v-if="!isPublicReadOnly" class="icon-action-light" type="button" aria-label="Download all" @click="downloadAllDocuments">
              <Icon name="lucide:archive" />
            </button>
          </div>
        </div>

        <div class="document-tree-scroll">
          <p v-if="isPublicReadOnly && !allowGuestDocumentAccess" class="rounded-2xl border border-dashed border-cream bg-white px-4 py-5 text-sm text-olive">
            {{ text.organizationPublic.guestDocumentDisabled }}
          </p>

          <DocumentTreeNode
            v-for="node in documentTree"
            :key="node.id"
            :node="node"
            :depth="0"
            :selected-document-id="selectedDocumentId"
            :expanded-ids="expandedIds"
            :read-only="isPublicReadOnly"
            @toggle="toggleFolder"
            @open-file="openDocumentNode"
            @add-folder="promptCreateFolder"
            @add-file="openUploadModal"
            @download="downloadNode"
            @rename="renameNode"
            @delete="deleteNode"
          />

          <p v-if="!documentTree.length && (!isPublicReadOnly || allowGuestDocumentAccess)" class="rounded-2xl border border-dashed border-cream bg-white px-4 py-5 text-sm text-olive">
            {{ text.documents.emptyTree }}
          </p>
        </div>
      </article>

      <div class="document-resize-handle" role="separator" aria-orientation="vertical" @pointerdown="startTreeResize" />

      <section class="surface-card document-view-panel">
        <div v-if="openDocuments.length" class="document-tabs">
          <div
            v-for="document in openDocuments"
            :key="document.id"
            :class="['document-tab', selectedDocumentId === document.id && 'active']"
          >
            <button class="document-tab-select" type="button" @click="selectDocument(document)">
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
            <div v-if="!isPublicReadOnly" class="document-analysis-actions">
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
              <div class="analysis-ring-grid">
                <div class="analysis-ring" :style="getAnalysisRingStyle(selectedDocument, 'parse')">
                  <span>{{ getAnalysisProgress(selectedDocument, 'parse') }}%</span>
                </div>
                <div class="analysis-ring" :style="getAnalysisRingStyle(selectedDocument, 'graph')">
                  <span>{{ getAnalysisProgress(selectedDocument, 'graph') }}%</span>
                </div>
              </div>
            </div>
          </div>

          <section v-if="!isPublicReadOnly" class="document-analysis-panel" aria-label="Document analysis progress">
            <p v-if="analysisActionError || downloadError || error" class="document-analysis-error">
              {{ analysisActionError || downloadError || error }}
            </p>
            <div class="document-analysis-summary">
              <div>
                <p class="section-kicker">Pipeline</p>
                <strong>{{ selectedDocument.analysis?.message || getAnalysisStateLabel(selectedDocument) }}</strong>
              </div>
              <span v-if="selectedDocument.analysis?.locked" class="status-badge status-warning">Đang khóa xử lý</span>
              <span v-else class="status-badge status-info">Có thể xử lý</span>
            </div>
          </section>

          <article :class="['document-preview', selectedDocumentPreview?.kind === 'text' && 'text-preview-mode']">
            <p>{{ text.documents.previewLead }}</p>
            <iframe
              v-if="isPdfDocument(selectedDocument) && getDocumentContentUrl(selectedDocument)"
              :src="getDocumentContentUrl(selectedDocument)"
              class="document-preview-frame"
              :title="selectedDocument.title"
            />
            <img
              v-else-if="isImageDocument(selectedDocument) && getDocumentContentUrl(selectedDocument)"
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
      v-if="!isPublicReadOnly"
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

        <p v-if="remediationQuestion" class="upload-remediation-note">
          Tài liệu sau khi tải lên sẽ được kiểm tra lại với câu hỏi: "{{ remediationQuestion }}"
        </p>

        <p v-if="uploadValidationError" class="upload-validation-error">
          {{ uploadValidationError }}
        </p>

        <p v-if="remediationResultMessage" class="upload-remediation-note">
          {{ remediationResultMessage }}
        </p>

        <div class="upload-scope-grid">
          <button
            type="button"
            :class="['upload-scope-option', uploadVisibility === 'public' && 'active']"
            @click="uploadVisibility = 'public'"
          >
            <Icon name="lucide:globe-2" />
            <span>Public</span>
            <small>Khach hang co the hoi tren chat tu van.</small>
          </button>
          <button
            type="button"
            :class="['upload-scope-option', uploadVisibility === 'private' && 'active']"
            @click="uploadVisibility = 'private'"
          >
            <Icon name="lucide:lock" />
            <span>Private</span>
            <small>Chi nhan vien co quyen moi duoc hoi.</small>
          </button>
        </div>

        <div v-if="pendingUploads.length" class="upload-file-list">
          <div v-for="file in pendingUploads" :key="`${file.name}-${file.size}`" class="upload-file-row">
            <Icon :name="getDocumentIcon(file.name)" />
            <span>{{ file.name }}</span>
          </div>
        </div>

        <footer class="modal-footer">
          <button v-if="pendingUploads.length" class="btn-secondary" type="button" @click="pendingUploads = []">{{ text.documents.changeFiles }}</button>
          <button class="btn-secondary" type="button" @click="clearUploadModal">{{ text.common.cancel }}</button>
          <button class="btn-primary" type="button" :disabled="!pendingUploads.length || isSavingTree || isUploadProcessing" @click="handleUpload">
            <Icon v-if="isUploadProcessing" name="lucide:loader-circle" class="upload-spinner" />
            {{ isUploadProcessing ? 'Đang tải tài liệu...' : text.documents.upload }}
          </button>
        </footer>
      </div>
    </AppPopup>
  </div>
</template>

<script setup lang="ts">
import DocumentTreeNode from '@/components/documents/DocumentTreeNode.vue'
import type { KnowledgeDocument, OrganizationDocumentTreeNode, OrganizationSummary } from '@/types/organization'

definePageMeta({
  layout: 'org',
  orgFullBleed: true
})

const { text } = useAppLocale()

const route = useRoute()
const { isAuthenticated } = useAuth()
const { loadOrganizations, getOrganizationBySlug } = useOrganization()
const settingsApi = useApiOrganizationSettings()
const documentsApi = useApiDocuments()
const {
  error,
  getDocuments,
  getOpenDocumentIds,
  getSelectedDocumentId,
  getPreview,
  loadDocuments,
  loadPublicDocuments,
  uploadDocument,
  startAnalysis,
  stopAnalysis,
  deleteDocument: deleteDocumentFromStore,
  openDocument: openDocumentInStore,
  selectDocument: selectDocumentInStore,
  closeDocument: closeDocumentInStore,
  closeAllDocuments: closeAllDocumentsInStore
} = useDocuments()

const slug = computed(() => String(route.params.slug ?? route.params.id ?? ''))
const { data: publicData } = await useFetch<{
  organization: OrganizationSummary
  allowGuestDocumentAccess: boolean
  documentTree: OrganizationDocumentTreeNode[]
}>(() => `/api/public/organizations/${slug.value}`)
const memberOrganization = computed(() => getOrganizationBySlug(slug.value))
const organization = computed(() => memberOrganization.value ?? publicData.value?.organization)
const allowGuestDocumentAccess = computed(() => publicData.value?.allowGuestDocumentAccess ?? false)
const isPublicReadOnly = computed(() => !memberOrganization.value)
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
const uploadVisibility = ref<'public' | 'private'>('private')
const uploadValidationError = ref<string | null>(null)
const remediationResultMessage = ref<string | null>(null)
const isUploadProcessing = ref(false)
const isRemediationChecking = ref(false)
const analysisActionError = ref<string | null>(null)
const downloadError = ref<string | null>(null)
const isSavingTree = ref(false)
const treePanelWidth = ref(380)
let analysisPollTimer: ReturnType<typeof setInterval> | null = null

const SUPPORTED_UPLOAD_EXTENSIONS = new Set(['pdf', 'docx', 'xlsx', 'csv', 'txt'])
const SUPPORTED_UPLOAD_ACCEPT = '.pdf,.docx,.xlsx,.csv,.txt'
const remediationQuestion = computed(() => typeof route.query.feedbackQuestion === 'string' ? route.query.feedbackQuestion.trim() : '')

const normalizeNode = (node: OrganizationDocumentTreeNode, parentId: string | null = null): OrganizationDocumentTreeNode => ({
  id: node.id,
  type: node.type,
  name: node.name,
  parentId,
  documentId: node.documentId ?? null,
  children: node.type === 'folder' ? (node.children ?? []).map((child) => normalizeNode(child, node.id)) : undefined
})

const cloneTree = (nodes: OrganizationDocumentTreeNode[]) => nodes.map((node) => normalizeNode(node, node.parentId ?? null))

const ensureDefaultFolders = (nodes: OrganizationDocumentTreeNode[]) => {
  if (isPublicReadOnly.value) {
    return nodes
  }

  const nextNodes = [...nodes]
  if (!nextNodes.some((node) => node.id === 'public-documents')) {
    nextNodes.unshift({ id: 'public-documents', type: 'folder', name: 'Public', parentId: null, children: [] })
  }
  if (!nextNodes.some((node) => node.id === 'private-documents')) {
    nextNodes.push({ id: 'private-documents', type: 'folder', name: 'Private', parentId: null, children: [] })
  }
  return nextNodes
}

const buildDocumentNodes = (visibility: 'public' | 'private') =>
  documents.value
    .filter((document) => document.visibility === visibility)
    .map<OrganizationDocumentTreeNode>((document) => ({
    id: `document-${document.id}`,
    type: 'file',
    name: document.title,
    parentId: `${visibility}-documents`,
    documentId: document.id
  }))

const buildFallbackTree = (): OrganizationDocumentTreeNode[] => [
  {
    id: 'public-documents',
    type: 'folder',
    name: 'Public',
    parentId: null,
    children: buildDocumentNodes('public')
  },
  {
    id: 'private-documents',
    type: 'folder',
    name: 'Private',
    parentId: null,
    children: isPublicReadOnly.value ? [] : buildDocumentNodes('private')
  }
].filter((node) => !isPublicReadOnly.value || node.id === 'public-documents')

const scopedDocumentTree = computed(() => {
  const sourceTree = treeState.value.length ? treeState.value : buildFallbackTree()
  if (isPublicReadOnly.value) {
    return sourceTree.filter((node) => node.id === 'public-documents')
  }

  const publicNode = sourceTree.find((node) => node.id === 'public-documents')
  const privateNode = sourceTree.find((node) => node.id === 'private-documents')
  return [
    publicNode ?? { id: 'public-documents', type: 'folder' as const, name: 'Public', parentId: null, children: [] },
    privateNode ?? { id: 'private-documents', type: 'folder' as const, name: 'Private', parentId: null, children: [] }
  ]
})
const documentTree = computed(() => scopedDocumentTree.value)
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

const seedExpandedFolders = (nodes: OrganizationDocumentTreeNode[]) => {
  const seedFolders = new Set<string>()
  const collectFolders = (nextNodes: OrganizationDocumentTreeNode[]) => {
    for (const node of nextNodes) {
      if (node.type === 'folder') {
        seedFolders.add(node.id)
        collectFolders(node.children ?? [])
      }
    }
  }

  collectFolders(nodes)
  expandedFolders.value = seedFolders
}

const setTreeState = (nodes: OrganizationDocumentTreeNode[]) => {
  treeState.value = ensureDefaultFolders(nodes.map((node) => normalizeNode(node)))
  seedExpandedFolders(treeState.value)
}

const persistTree = async (nextTree: OrganizationDocumentTreeNode[]) => {
  if (isPublicReadOnly.value) {
    return
  }

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
  const rawTree = Array.isArray(response.settings.documentTree) ? response.settings.documentTree : []
  const prunedTree = pruneMissingDocumentNodes(rawTree)
  setTreeState(prunedTree)
  if (JSON.stringify(rawTree) !== JSON.stringify(prunedTree)) {
    await persistTree(prunedTree)
  }
}

const loadPublicTree = () => {
  setTreeState(pruneMissingDocumentNodes(Array.isArray(publicData.value?.documentTree) ? publicData.value.documentTree : []))
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

const removeNode = (nodes: OrganizationDocumentTreeNode[], targetId: string): OrganizationDocumentTreeNode[] =>
  nodes
    .filter((node) => node.id !== targetId)
    .map((node) => ({
      ...node,
      children: node.children ? removeNode(node.children, targetId) : node.children
    }))

const removeDocumentNodesByIds = (nodes: OrganizationDocumentTreeNode[], documentIds: Set<string>): OrganizationDocumentTreeNode[] =>
  nodes
    .filter((node) => node.type !== 'file' || !node.documentId || !documentIds.has(node.documentId))
    .map((node) => ({
      ...node,
      children: node.children ? removeDocumentNodesByIds(node.children, documentIds) : node.children
    }))

const pruneMissingDocumentNodes = (nodes: OrganizationDocumentTreeNode[]): OrganizationDocumentTreeNode[] => {
  const existingDocumentIds = new Set(documents.value.map((document) => document.id))
  return nodes
    .filter((node) => node.type !== 'file' || (node.documentId && existingDocumentIds.has(node.documentId)))
    .map((node) => ({
      ...node,
      children: node.children ? pruneMissingDocumentNodes(node.children) : node.children
    }))
}

const isRootScopeNode = (nodeId: string) => nodeId === 'public-documents' || nodeId === 'private-documents'

const promptCreateFolder = async (parentId: string | null) => {
  if (isPublicReadOnly.value || !parentId) {
    return
  }

  const parentNode = findNode(documentTree.value, parentId)
  if (!parentNode || parentNode.type !== 'folder') {
    return
  }

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

  expandedFolders.value = new Set([...expandedFolders.value, parentId, nextNode.id])
  await persistTree(appendNode(documentTree.value, parentId, nextNode))
}

const renameNode = async (nodeId: string) => {
  if (isPublicReadOnly.value) {
    return
  }

  const currentNode = findNode(documentTree.value, nodeId)
  if (!currentNode || isRootScopeNode(currentNode.id)) {
    return
  }

  const name = window.prompt(text.documents.renamePrompt, currentNode.name)
  if (!name?.trim()) {
    return
  }

  await persistTree(withTreeMutation(documentTree.value, nodeId, (node) => ({ ...node, name: name.trim() })))
}

const deleteNode = async (node: OrganizationDocumentTreeNode) => {
  if (isPublicReadOnly.value || isRootScopeNode(node.id)) {
    return
  }

  const confirmMessage = node.type === 'folder'
    ? `Xóa folder "${node.name}" và toàn bộ file bên trong khỏi hệ thống?`
    : `Xóa file "${node.name}" khỏi hệ thống?`
  if (!window.confirm(confirmMessage)) {
    return
  }

  const documentIds = collectFileNodes(node)
    .map((fileNode) => fileNode.documentId)
    .filter((documentId): documentId is string => Boolean(documentId))

  for (const documentId of documentIds) {
    try {
      await deleteDocumentFromStore(slug.value, documentId)
      closeDocument(documentId)
    } catch (err) {
      downloadError.value = getActionErrorMessage(err, 'Khong xoa duoc tai lieu.')
      return
    }
  }

  await loadDocuments(slug.value)
  const deletedDocumentIds = new Set(documentIds)
  const nextTree = node.type === 'folder'
    ? removeNode(documentTree.value, node.id)
    : removeDocumentNodesByIds(documentTree.value, deletedDocumentIds)
  await persistTree(pruneMissingDocumentNodes(nextTree))
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
    await openDocumentInStore(slug.value, document, { public: isPublicReadOnly.value })
  }
}

const selectDocument = async (document: KnowledgeDocument) => {
  await selectDocumentInStore(slug.value, document, { public: isPublicReadOnly.value })
}

const sanitizeFileName = (value: string) =>
  value.replace(/[<>:"/\\|?*\x00-\x1F]/g, '_').replace(/\s+/g, ' ').trim() || 'download'

const triggerDownload = (blob: Blob, fileName: string) => {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = sanitizeFileName(fileName)
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

const crcTable = (() => {
  const table = new Uint32Array(256)
  for (let index = 0; index < 256; index += 1) {
    let value = index
    for (let bit = 0; bit < 8; bit += 1) {
      value = (value & 1) ? (0xEDB88320 ^ (value >>> 1)) : (value >>> 1)
    }
    table[index] = value >>> 0
  }
  return table
})()

const crc32 = (bytes: Uint8Array) => {
  let crc = 0xFFFFFFFF
  for (const byte of bytes) {
    crc = crcTable[(crc ^ byte) & 0xFF] ^ (crc >>> 8)
  }
  return (crc ^ 0xFFFFFFFF) >>> 0
}

const writeUInt16 = (target: number[], value: number) => {
  target.push(value & 0xFF, (value >>> 8) & 0xFF)
}

const writeUInt32 = (target: number[], value: number) => {
  target.push(value & 0xFF, (value >>> 8) & 0xFF, (value >>> 16) & 0xFF, (value >>> 24) & 0xFF)
}

const createZipBlob = (files: Array<{ name: string, data: Uint8Array }>) => {
  const encoder = new TextEncoder()
  const chunks: Uint8Array[] = []
  const centralDirectory: number[] = []
  let offset = 0

  for (const file of files) {
    const nameBytes = encoder.encode(file.name)
    const checksum = crc32(file.data)
    const localHeader: number[] = []

    writeUInt32(localHeader, 0x04034B50)
    writeUInt16(localHeader, 20)
    writeUInt16(localHeader, 0)
    writeUInt16(localHeader, 0)
    writeUInt16(localHeader, 0)
    writeUInt16(localHeader, 0)
    writeUInt32(localHeader, checksum)
    writeUInt32(localHeader, file.data.length)
    writeUInt32(localHeader, file.data.length)
    writeUInt16(localHeader, nameBytes.length)
    writeUInt16(localHeader, 0)

    chunks.push(new Uint8Array(localHeader), nameBytes, file.data)

    writeUInt32(centralDirectory, 0x02014B50)
    writeUInt16(centralDirectory, 20)
    writeUInt16(centralDirectory, 20)
    writeUInt16(centralDirectory, 0)
    writeUInt16(centralDirectory, 0)
    writeUInt16(centralDirectory, 0)
    writeUInt16(centralDirectory, 0)
    writeUInt32(centralDirectory, checksum)
    writeUInt32(centralDirectory, file.data.length)
    writeUInt32(centralDirectory, file.data.length)
    writeUInt16(centralDirectory, nameBytes.length)
    writeUInt16(centralDirectory, 0)
    writeUInt16(centralDirectory, 0)
    writeUInt16(centralDirectory, 0)
    writeUInt16(centralDirectory, 0)
    writeUInt32(centralDirectory, 0)
    writeUInt32(centralDirectory, offset)
    centralDirectory.push(...nameBytes)

    offset += localHeader.length + nameBytes.length + file.data.length
  }

  const centralOffset = offset
  const centralBytes = new Uint8Array(centralDirectory)
  const endRecord: number[] = []
  writeUInt32(endRecord, 0x06054B50)
  writeUInt16(endRecord, 0)
  writeUInt16(endRecord, 0)
  writeUInt16(endRecord, files.length)
  writeUInt16(endRecord, files.length)
  writeUInt32(endRecord, centralBytes.length)
  writeUInt32(endRecord, centralOffset)
  writeUInt16(endRecord, 0)

  return new Blob([...chunks, centralBytes, new Uint8Array(endRecord)], { type: 'application/zip' })
}

const downloadDocument = async (document: KnowledgeDocument) => {
  if (isPublicReadOnly.value) {
    return
  }

  downloadError.value = null
  try {
    const response = await documentsApi.downloadUrl(slug.value, document.id)
    const fileResponse = await fetch(response.download_url)
    if (!fileResponse.ok) {
      throw new Error(fileResponse.statusText)
    }
    triggerDownload(await fileResponse.blob(), document.title)
  } catch (err) {
    downloadError.value = getActionErrorMessage(err, 'Không tải được tài liệu.')
  }
}

const collectFileNodes = (node: OrganizationDocumentTreeNode): OrganizationDocumentTreeNode[] => {
  if (node.type === 'file') {
    return node.documentId ? [node] : []
  }
  return (node.children ?? []).flatMap(collectFileNodes)
}

const downloadNode = async (node: OrganizationDocumentTreeNode) => {
  if (isPublicReadOnly.value) {
    return
  }

  if (node.type === 'file') {
    const document = node.documentId ? documentsById.value.get(node.documentId) : null
    if (document) {
      await downloadDocument(document)
    }
    return
  }

  const fileNodes = collectFileNodes(node)
  if (!fileNodes.length) {
    downloadError.value = 'Folder không có file để tải.'
    return
  }

  downloadError.value = null
  try {
    const files = []
    for (const fileNode of fileNodes) {
      const document = fileNode.documentId ? documentsById.value.get(fileNode.documentId) : null
      if (!document) {
        continue
      }
      const response = await documentsApi.downloadUrl(slug.value, document.id)
      const fileResponse = await fetch(response.download_url)
      if (!fileResponse.ok) {
        throw new Error(fileResponse.statusText)
      }
      files.push({
        name: sanitizeFileName(fileNode.name || document.title),
        data: new Uint8Array(await fileResponse.arrayBuffer())
      })
    }

    triggerDownload(createZipBlob(files), `${node.name}.zip`)
  } catch (err) {
    downloadError.value = getActionErrorMessage(err, 'Không tải được folder.')
  }
}

const downloadAllDocuments = async () => {
  await downloadNode({
    id: 'all-documents',
    type: 'folder',
    name: organization.value?.name || 'documents',
    parentId: null,
    children: documentTree.value
  })
}

const inferVisibilityFromParent = (parentId: string | null): 'public' | 'private' => {
  if (parentId === 'public-documents') {
    return 'public'
  }
  if (parentId === 'private-documents') {
    return 'private'
  }

  const parentNode = parentId ? findNode(documentTree.value, parentId) : null
  const parentName = parentNode?.name.toLowerCase() || ''
  return parentName.includes('public') ? 'public' : 'private'
}

const openUploadModal = (parentId: string | null) => {
  if (isPublicReadOnly.value) {
    return
  }

  uploadParentId.value = parentId
  uploadVisibility.value = inferVisibilityFromParent(parentId)
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
  uploadVisibility.value = 'private'
  uploadValidationError.value = null
  remediationResultMessage.value = null
  isDragging.value = false
  isUploadOpen.value = false
}

const finishUploadModal = () => {
  pendingUploads.value = []
  uploadParentId.value = null
  uploadVisibility.value = 'private'
  uploadValidationError.value = null
  isDragging.value = false
  isUploadOpen.value = false
}

const verifyRemediationQuestion = async () => {
  if (!remediationQuestion.value) {
    return
  }

  try {
    const response = await documentsApi.searchOrganization(slug.value, remediationQuestion.value, 5)
    remediationResultMessage.value = response.count > 0
      ? 'Đúng: tài liệu khắc phục có nội dung liên quan đến câu hỏi phản hồi.'
      : 'Sai: tài liệu khắc phục chưa có nội dung liên quan đến câu hỏi phản hồi.'
  } catch {
    remediationResultMessage.value = 'Sai: hệ thống không xác minh được tài liệu khắc phục.'
  }
}

const waitForAnalysisAttempt = async (documentIds: string[]) => {
  if (!documentIds.length) {
    return
  }

  const maxAttempts = 8
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    await new Promise((resolve) => setTimeout(resolve, 1500))
    await loadDocuments(slug.value)
    const pendingDocuments = documents.value.filter((document) =>
      documentIds.includes(document.id) && isAnalysisRunning(document)
    )
    if (!pendingDocuments.length) {
      return
    }
  }
}

const runRemediationCheckInBackground = async (documentIds: string[]) => {
  if (!remediationQuestion.value) {
    return
  }

  remediationResultMessage.value = null
  isRemediationChecking.value = true
  try {
    await waitForAnalysisAttempt(documentIds)
    await verifyRemediationQuestion()
  } finally {
    isRemediationChecking.value = false
  }
}

const handleUpload = async () => {
  if (isPublicReadOnly.value) {
    return
  }

  isUploadProcessing.value = true
  try {
    const hadPersistedTree = treeState.value.length > 0

    for (const file of pendingUploads.value) {
      await uploadDocument(slug.value, file, uploadVisibility.value)
    }

    await loadDocuments(slug.value)
    const uploadedDocuments = pendingUploads.value
      .map((file) => documents.value.find((document) => document.title === file.name && document.visibility === uploadVisibility.value))
      .filter((document): document is KnowledgeDocument => Boolean(document))

    for (const document of uploadedDocuments) {
      try {
        await startAnalysis(slug.value, document.id)
      } catch {
        // The backend may reject analysis for documents that are already processing or not backed by storage metadata.
      }
    }

    if (!hadPersistedTree && !uploadParentId.value) {
      await persistTree(buildFallbackTree())
      finishUploadModal()
      void runRemediationCheckInBackground(uploadedDocuments.map((document) => document.id))
      return
    }

    let nextTree = documentTree.value
    const effectiveParentId = uploadParentId.value ?? `${uploadVisibility.value}-documents`
    for (const document of uploadedDocuments) {
      nextTree = appendNode(nextTree, effectiveParentId, {
        id: `document-${document.id}`,
        type: 'file',
        name: document.title,
        parentId: effectiveParentId,
        documentId: document.id
      })
    }

    await persistTree(nextTree)
    finishUploadModal()
    void runRemediationCheckInBackground(uploadedDocuments.map((document) => document.id))
  } finally {
    isUploadProcessing.value = false
  }
}

const getActionErrorMessage = (err: unknown, fallback: string) => {
  if (err && typeof err === 'object' && 'data' in err) {
    const data = (err as { data?: { detail?: string, message?: string, statusMessage?: string } }).data
    return data?.detail || data?.message || data?.statusMessage || fallback
  }

  return err instanceof Error ? err.message : fallback
}

const handleStartAnalysis = async (document: KnowledgeDocument) => {
  if (isPublicReadOnly.value) {
    return
  }

  analysisActionError.value = null

  try {
    await startAnalysis(slug.value, document.id)
  } catch (err) {
    analysisActionError.value = getActionErrorMessage(err, 'Không bắt đầu được phân tích tài liệu.')
  }
}

const handleStopAnalysis = async (document: KnowledgeDocument) => {
  if (isPublicReadOnly.value) {
    return
  }

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

const getAnalysisRingStyle = (document: KnowledgeDocument, key: 'parse' | 'graph') => ({
  background: `conic-gradient(#2f5f9f ${getAnalysisProgress(document, key)}%, rgba(0,0,0,0.08) 0)`
})

const startTreeResize = (event: PointerEvent) => {
  const startX = event.clientX
  const startWidth = treePanelWidth.value
  const handlePointerMove = (moveEvent: PointerEvent) => {
    treePanelWidth.value = Math.min(620, Math.max(280, startWidth + moveEvent.clientX - startX))
  }
  const handlePointerUp = () => {
    window.removeEventListener('pointermove', handlePointerMove)
    window.removeEventListener('pointerup', handlePointerUp)
  }

  window.addEventListener('pointermove', handlePointerMove)
  window.addEventListener('pointerup', handlePointerUp)
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
  if (isAuthenticated.value) {
    await loadOrganizations()
  }

  if (memberOrganization.value) {
    await loadDocuments(slug.value)
    await loadTree()

    analysisPollTimer = setInterval(() => {
      if (documents.value.some(isAnalysisRunning)) {
        void loadDocuments(slug.value)
      }
    }, 3000)
    return
  }

  if (allowGuestDocumentAccess.value) {
    await loadPublicDocuments(slug.value)
    loadPublicTree()
  }
})

onBeforeUnmount(() => {
  if (analysisPollTimer) {
    clearInterval(analysisPollTimer)
    analysisPollTimer = null
  }
})
</script>
