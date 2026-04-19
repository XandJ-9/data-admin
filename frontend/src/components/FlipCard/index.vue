<template>
  <div class="flip-card" :style="{ minHeight: minHeight }">
    <div class="flip-card-inner" :class="{ flipped }">
      <div class="flip-card-front" :class="{ active: !flipped, inactive: flipped }">
        <slot name="front" />
      </div>
      <div class="flip-card-back" :class="{ active: flipped, inactive: !flipped }">
        <slot name="back" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  flipped: {
    type: Boolean,
    default: false,
  },
  minHeight: {
    type: String,
    default: '400px',
  },
})
</script>

<style scoped lang="scss">
.flip-card {
  perspective: 1200px;
  width: 100%;

  .flip-card-inner {
    position: relative;
    width: 100%;
    min-height: inherit;
    transition: transform 0.6s ease;
    transform-style: preserve-3d;

    &.flipped {
      transform: rotateY(180deg);
    }
  }

  .flip-card-front,
  .flip-card-back {
    width: 100%;
    min-height: inherit;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
  }

  .flip-card-front {
    position: relative;
  }

  .flip-card-back {
    position: absolute;
    top: 0;
    left: 0;
    transform: rotateY(180deg) translateZ(1px);
  }

  .active {
    pointer-events: auto;
    z-index: 2;
  }

  .inactive {
    pointer-events: none;
    z-index: 1;
  }
}
</style>
