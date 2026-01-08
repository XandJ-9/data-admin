<template>
   <i-frame :src="url"></i-frame>
</template>

<script setup>
import iFrame from '@/components/iFrame'

const url = import.meta.env.VITE_APP_BASE_API + "/docs/"
</script>
