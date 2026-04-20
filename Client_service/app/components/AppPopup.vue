<template>
  <component :is="tag" ref="rootRef" :class="rootClass">
    <slot name="trigger" :open="open" :toggle="toggle" :close="close" />

    <Teleport v-if="teleport" :to="teleportTo">
      <Transition :name="backdropTransitionName">
        <div v-if="open && backdropClass" :class="backdropClass" @click="handleBackdropClick" />
      </Transition>

      <Transition :name="transitionName">
        <div v-if="open" ref="contentRef" :class="contentClass" @click.self="handleContentSelfClick">
          <slot :close="close" />
        </div>
      </Transition>
    </Teleport>

    <Transition v-else :name="transitionName">
      <div v-if="open" ref="contentRef" :class="contentClass" @click.self="handleContentSelfClick">
        <slot :close="close" />
      </div>
    </Transition>
  </component>
</template>

<script setup lang="ts">
const open = defineModel<boolean>('open', { default: false })

const props = withDefaults(
  defineProps<{
    tag?: string
    rootClass?: string
    contentClass?: string
    transitionName?: string
    backdropClass?: string
    backdropTransitionName?: string
    teleport?: boolean
    teleportTo?: string
    closeOnContentSelf?: boolean
    closeOnOutside?: boolean
    closeOnBackdrop?: boolean
  }>(),
  {
    tag: 'div',
    rootClass: '',
    contentClass: '',
    transitionName: 'menu',
    backdropClass: '',
    backdropTransitionName: 'fade',
    teleport: false,
    teleportTo: 'body',
    closeOnContentSelf: false,
    closeOnOutside: true,
    closeOnBackdrop: true
  }
)

const rootRef = ref<HTMLElement | null>(null)
const contentRef = ref<HTMLElement | null>(null)

const close = () => {
  open.value = false
}

const toggle = () => {
  open.value = !open.value
}

const handleContentSelfClick = () => {
  if (props.closeOnContentSelf) {
    close()
  }
}

const handleBackdropClick = () => {
  if (props.closeOnBackdrop) {
    close()
  }
}

const handleOutsidePointerDown = (event: PointerEvent) => {
  if (!open.value || !props.closeOnOutside) {
    return
  }

  const target = event.target as Node | null
  if (!target) {
    return
  }

  if (rootRef.value?.contains(target) || contentRef.value?.contains(target)) {
    return
  }

  close()
}

onMounted(() => {
  document.addEventListener('pointerdown', handleOutsidePointerDown, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleOutsidePointerDown, true)
})
</script>
