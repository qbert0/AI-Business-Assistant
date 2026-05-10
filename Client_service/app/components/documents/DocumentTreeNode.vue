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
        <span class="truncate">{{ node.name }}</span>
      </button>

      <button
        v-else
        class="flex min-w-0 flex-1 items-center gap-2 text-left"
        type="button"
        @click="$emit('open-file', node)"
      >
        <Icon name="lucide:file-text" />
        <span class="truncate">{{ node.name }}</span>
      </button>

      <div class="flex items-center gap-1">
        <button
          v-if="node.type === 'folder'"
          class="icon-action-light"
          type="button"
          :aria-label="text.documents.addFolder"
          @click="$emit('add-folder', node.id)"
        >
          <Icon name="lucide:folder-plus" />
        </button>
        <button
          v-if="node.type === 'folder'"
          class="icon-action-light"
          type="button"
          :aria-label="text.documents.addFile"
          @click="$emit('add-file', node.id)"
        >
          <Icon name="lucide:file-plus" />
        </button>
        <button class="icon-action-light" type="button" :aria-label="text.common.rename" @click="$emit('rename', node.id)">
          <Icon name="lucide:pencil" />
        </button>
      </div>
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
        @toggle="$emit('toggle', $event)"
        @open-file="$emit('open-file', $event)"
        @add-folder="$emit('add-folder', $event)"
        @add-file="$emit('add-file', $event)"
        @rename="$emit('rename', $event)"
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
}>()

defineEmits<{
  toggle: [nodeId: string]
  'open-file': [node: OrganizationDocumentTreeNode]
  'add-folder': [parentId: string]
  'add-file': [parentId: string]
  rename: [nodeId: string]
}>()

const childNodes = computed(() => props.node.children ?? [])
const isExpanded = computed(() => props.expandedIds.includes(props.node.id))
</script>
