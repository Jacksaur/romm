<script setup>
import { inject } from "vue";

// Props
const props = defineProps(["rail"]);

// Event listeners bus
const emitter = inject("emitter");
</script>

<template>
  <v-btn
    @click="emitter.emit('toggleDrawerRail')"
    rounded="0"
    color="primary"
    block
  >
    <v-icon v-if="rail">mdi-arrow-collapse-right</v-icon>
    <v-icon v-if="!rail">mdi-arrow-collapse-left</v-icon>
  </v-btn>
</template>
