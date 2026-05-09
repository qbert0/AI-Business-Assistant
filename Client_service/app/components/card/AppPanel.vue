<template>
  <section class="app-panel">
    <header
      v-if="$slots['header-left'] || $slots['header-right']"
      :class="['app-panel-header', !($slots.content || $slots.default) && 'no-content']"
    >
      <div class="app-panel-header-left">
        <slot name="header-left" />
      </div>
      <div v-if="$slots['header-right']" class="app-panel-header-right">
        <slot name="header-right" />
      </div>
    </header>

    <div v-if="$slots.content || $slots.default" class="app-panel-content">
      <slot name="content">
        <slot />
      </slot>
    </div>
  </section>
</template>
