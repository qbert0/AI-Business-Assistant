<template>
  <div class="space-y-2">
    <div
      :class="[
        'flex items-center gap-2 rounded-2xl border border-transparent px-3 py-2 transition',
        node.type === 'file' && selectedDocumentId === node.documentId ? 'bg-charcoal text-white' : 'bg-white hover:border-cream'
      ]"
      :style="{ marginLeft: `${depth * 14}px` }"
    >
      <button
        v-if="node.type === 'folder'"
        class="flex min-w-0 flex-1 items-center gap-2 text-left"
        type="button"
        @click="$emit('toggle', node.id)"
      >
        <Icon :name="isExpanded ? 'lucide:folder-open' : 'lucide:folder'" />
        <span class="truncate" :title="node.name">{{ node.name }}</span>
      </button>

      <button
        v-else
        class="flex min-w-0 flex-1 items-center gap-2 text-left"
        type="button"
        @click="$emit('open-file', node)"
      >
        <Icon name="lucide:file-text" />
        <span class="truncate" :title="node.name">{{ node.name }}</span>
      </button>

      <AppPopup v-if="!readOnly" root-class="relative" content-class="document-node-menu" match-trigger-position teleport>
        <template #trigger="{ toggle }">
          <button class="icon-action-light" type="button" :aria-label="text.chatSidebar.actions" @click.stop="toggle">
            <Icon name="lucide:more-horizontal" />
          </button>
        </template>

        <template #default="{ close }">
          <button
            v-if="node.type === 'folder'"
            class="document-node-menu-item"
            type="button"
            @click="emitNodeAction('add-folder', close)"
          >
            <Icon name="lucide:folder-plus" />
            <span>{{ text.documents.addFolder }}</span>
          </button>
          <button
            v-if="node.type === 'folder'"
            class="document-node-menu-item"
            type="button"
            @click="emitNodeAction('add-file', close)"
          >
            <Icon name="lucide:file-plus" />
            <span>{{ text.documents.addFile }}</span>
          </button>
          <button v-if="!isRootScope" class="document-node-menu-item" type="button" @click="emitNodeAction('download', close)">
            <Icon name="lucide:download" />
            <span>Download</span>
          </button>
          <button v-if="!isRootScope" class="document-node-menu-item" type="button" @click="emitNodeAction('rename', close)">
            <Icon name="lucide:pencil" />
            <span>{{ text.common.rename }}</span>
          </button>
          <button v-if="!isRootScope" class="document-node-menu-item danger" type="button" @click="emitNodeAction('delete', close)">
            <Icon name="lucide:trash-2" />
            <span>{{ text.common.delete }}</span>
          </button>
        </template>
      </AppPopup>
    </div>

    <div v-if="node.type === 'folder' && isExpanded" class="space-y-2">
      <p v-if="!childNodes.length" class="pl-4 text-caption text-olive" :style="{ marginLeft: `${depth * 14}px` }">
        {{ text.documents.emptyFolder }}
      </p>

      <DocumentTreeNode
        v-for="child in childNodes"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :selected-document-id="selectedDocumentId"
        :expanded-ids="expandedIds"
        :read-only="readOnly"
        @toggle="$emit('toggle', $event)"
        @open-file="$emit('open-file', $event)"
        @add-folder="$emit('add-folder', $event)"
        @add-file="$emit('add-file', $event)"
        @download="$emit('download', $event)"
        @rename="$emit('rename', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { OrganizationDocumentTreeNode } from '@/types/organization'

defineOptions({
  name: 'DocumentTreeNode'
})

const { text } = useAppLocale()

const props = defineProps<{
  node: OrganizationDocumentTreeNode
  depth: number
  selectedDocumentId: string | null
  expandedIds: string[]
  readOnly?: boolean
}>()

const emit = defineEmits<{
  toggle: [nodeId: string]
  'open-file': [node: OrganizationDocumentTreeNode]
  'add-folder': [parentId: string]
  'add-file': [parentId: string]
  download: [node: OrganizationDocumentTreeNode]
  rename: [nodeId: string]
  delete: [node: OrganizationDocumentTreeNode]
}>()

const childNodes = computed(() => props.node.children ?? [])
const isExpanded = computed(() => props.expandedIds.includes(props.node.id))
const isRootScope = computed(() => props.node.id === 'public-documents' || props.node.id === 'private-documents')

const emitNodeAction = (action: 'add-folder' | 'add-file' | 'download' | 'rename' | 'delete', close: () => void) => {
  close()
  if (action === 'add-folder') {
    emit('add-folder', props.node.id)
    return
  }
  if (action === 'add-file') {
    emit('add-file', props.node.id)
    return
  }
  if (action === 'download') {
    emit('download', props.node)
    return
  }
  if (action === 'delete') {
    emit('delete', props.node)
    return
  }
  emit('rename', props.node.id)
}
</script>
