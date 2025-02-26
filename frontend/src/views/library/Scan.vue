<script setup>
import { ref, inject } from "vue";
import socket from "@/services/socket.js";
import storePlatforms from "@/stores/platforms.js";
import storeScanning from "@/stores/scanning.js";
import PlatformIcon from "@/components/Platform/PlatformIcon.vue";

// Props
const platforms = storePlatforms();
const platformsToScan = ref([]);
const scanning = storeScanning();
const scannedPlatforms = ref([]);
const completeRescan = ref(false);

// Event listeners bus
const emitter = inject("emitter");

function scrollToBottom() {
  window.scrollTo(0, document.body.scrollHeight);
}

socket.on("scan:scanning_platform", ({ p_name, p_slug }) => {
  scannedPlatforms.value.push({
    name: p_name,
    slug: p_slug,
    roms: [],
  });
  window.setTimeout(scrollToBottom, 100);
});

socket.on("scan:scanning_rom", ({ p_slug, p_name, ...rom }) => {
  let platform = scannedPlatforms.value.find((p) => p.slug === p_slug);

  // Add the platform if the socket dropped and it's missing
  if (!platform) {
    scannedPlatforms.value.push({
      name: p_name,
      slug: p_slug,
      roms: [],
    });

    platform = scannedPlatforms.slice(-1);
  }

  platform.roms.push(rom);
  window.setTimeout(scrollToBottom, 100);
});

socket.on("scan:done", () => {
  scanning.set(false);
  
  emitter.emit("refreshPlatforms");
  emitter.emit("snackbarShow", {
    msg: "Scan completed successfully!",
    icon: "mdi-check-bold",
    color: "green",
  });
  socket.disconnect();
});

socket.on("scan:done_ko", (msg) => {
  scanning.set(false);

  emitter.emit("snackbarShow", {
    msg: `Scan couldn't be completed. Something went wrong: ${msg}`,
    icon: "mdi-close-circle",
    color: "red",
  });
  socket.disconnect();
});

// Functions
async function scan() {
  scanning.set(true);
  scannedPlatforms.value = [];

  if (!socket.connected) socket.connect();

  socket.emit(
    "scan",
    platformsToScan.value.map((p) => p.fs_slug).join(","),
    completeRescan.value
  );
}
</script>

<template>
  <!-- Platform selector -->
  <v-row class="pa-4" no-gutters>
    <v-select
      label="Platforms"
      item-title="name"
      v-model="platformsToScan"
      :items="platforms.value"
      variant="outlined"
      density="comfortable"
      multiple
      return-object
      clearable
      hide-details
      rounded="0"
      chips
    />
  </v-row>

  <!-- Complete rescan option -->
  <v-row class="pa-4" no-gutters>
    <v-checkbox
      v-model="completeRescan"
      label="Complete Rescan"
      prepend-icon="mdi-cached"
      hint="Rescan every rom, including already scanned roms"
      persistent-hint
    />
  </v-row>

  <!-- Scan button -->
  <v-row class="pa-4" no-gutters>
    <v-btn
      @click="scan()"
      :disabled="scanning.value"
      prepend-icon="mdi-magnify-scan"
      rounded="0"
    >
      <span v-if="!scanning.value">Scan</span>
      <v-progress-circular
        v-show="scanning.value"
        color="rommAccent1"
        class="ml-3 mr-2"
        :width="2"
        :size="20"
        indeterminate
      />
    </v-btn>
  </v-row>

  <v-divider
    class="border-opacity-100 ma-4"
    color="rommAccent1"
    :thickness="1"
  />

  <!-- Scan log -->
  <v-row
    no-gutters
    class="align-center pa-4"
    v-for="platform in scannedPlatforms"
  >
    <v-col>
      <v-avatar :rounded="0" size="40">
        <platform-icon :platform="platform"></platform-icon>
      </v-avatar>
      <span class="text-body-2 ml-5"> {{ platform.name }}</span>
      <v-list-item v-for="rom in platform.roms" class="text-body-2" disabled>
        <span v-if="rom.r_igdb_id" class="ml-10">
          • Identified <b>{{ rom.r_name }} 👾</b>
        </span>
        <span v-else class="ml-10">
          • {{ rom.file_name }} not found in IGDB
        </span>
      </v-list-item>
    </v-col>
  </v-row>
</template>
