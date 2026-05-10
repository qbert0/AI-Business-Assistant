<template>
  <component :is="tag" ref="rootRef" :class="rootClass">
    <slot name="trigger" :open="open" :toggle="toggle" :close="close" />

    <Teleport v-if="teleport" :to="teleportTo">
      <Transition :name="backdropTransitionName">
        <div v-if="open && backdropClass" :class="backdropClass" @click="handleBackdropClick" />
      </Transition>

      <Transition :name="transitionName">
        <div v-if="open" ref="contentRef" :class="contentClass" :style="floatingStyle" @click.self="handleContentSelfClick">
          <slot :close="close" />
        </div>
      </Transition>
    </Teleport>

    <Transition v-else :name="transitionName">
      <div v-if="open" ref="contentRef" :class="contentClass" :style="floatingStyle" @click.self="handleContentSelfClick">
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
    matchTriggerPosition?: boolean
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
    closeOnBackdrop: true,
    matchTriggerPosition: false
  }
)

const rootRef = ref<HTMLElement | null>(null)
const contentRef = ref<HTMLElement | null>(null)
const floatingStyle = ref<Record<string, string>>({})

const updateFloatingPosition = () => {
  if (!props.matchTriggerPosition || !props.teleport || !rootRef.value) {
    floatingStyle.value = {}
    return
  }

  const rect = rootRef.value.getBoundingClientRect()
  floatingStyle.value = {
    position: 'fixed',
    top: `${rect.bottom + 6}px`,
    right: `${Math.max(12, window.innerWidth - rect.right)}px`
  }
}

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
  window.addEventListener('resize', updateFloatingPosition)
  window.addEventListener('scroll', updateFloatingPosition, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleOutsidePointerDown, true)
  window.removeEventListener('resize', updateFloatingPosition)
  window.removeEventListener('scroll', updateFloatingPosition, true)
})

watch(open, async (value: boolean) => {
  if (value) {
    await nextTick()
    updateFloatingPosition()
  } else {
    floatingStyle.value = {}
  }
})
</script>
