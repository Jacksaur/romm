<script setup>
import { ref, inject } from "vue";
import { useDisplay } from "vuetify";
import { updateRomApi } from "@/services/api.js";

const { xs, mdAndDown, lgAndUp } = useDisplay();
const show = ref(false);
const rom = ref();
const renameAsIGDB = ref(false);

const emitter = inject("emitter");
emitter.on("showEditDialog", (romToEdit) => {
  show.value = true;
  rom.value = romToEdit;
});

async function updateRom(updatedData = { ...rom.value }) {
  show.value = false;
  emitter.emit("showLoadingDialog", { loading: true, scrim: true });

  await updateRomApi(rom.value, updatedData, renameAsIGDB.value)
    .then((response) => {
      emitter.emit("snackbarShow", {
        msg: response.data.msg,
        icon: "mdi-check-bold",
        color: "green",
      });
      emitter.emit("refreshGallery");
    })
    .catch((error) => {
      emitter.emit("snackbarShow", {
        msg: error.response.data.detail,
        icon: "mdi-close-circle",
        color: "red",
      });
    })
    .finally(() => {
      emitter.emit("showLoadingDialog", { loading: false, scrim: false });
    });
}
</script>

<template>
  <v-dialog
    :modelValue="show"
    scroll-strategy="none"
    width="auto"
    :scrim="false"
    @click:outside="show = false"
    @keydown.esc="show = false"
    no-click-animation
    persistent
  >
    <v-card
      rounded="0"
      :class="{
        'edit-content': lgAndUp,
        'edit-content-tablet': mdAndDown,
        'edit-content-mobile': xs,
      }"
    >
      <v-toolbar density="compact" class="bg-primary">
        <v-row class="align-center" no-gutters>
          <v-col cols="9" xs="9" sm="10" md="10" lg="11">
            <v-icon icon="mdi-pencil-box" class="ml-5" />
          </v-col>
          <v-col>
            <v-btn
              @click="show = false"
              class="bg-primary"
              rounded="0"
              variant="text"
              icon="mdi-close"
              block
            />
          </v-col>
        </v-row>
      </v-toolbar>
      <v-divider class="border-opacity-25" :thickness="1" />

      <v-card-text class="bg-secondary scroll">
        <v-row class="justify-center pa-2" no-gutters>
          <v-text-field
            @keyup.enter="updateRom()"
            v-model="rom.r_name"
            label="Name"
            variant="outlined"
            required
            hide-details
          />
        </v-row>
        <v-row class="justify-center pa-2" no-gutters>
          <v-text-field
            @keyup.enter="updateRom()"
            v-model="rom.file_name"
            label="File name"
            variant="outlined"
            required
            hide-details
          />
        </v-row>
        <v-row class="justify-center pa-2" no-gutters>
          <v-textarea
            @keyup.enter="updateRom()"
            v-model="rom.summary"
            label="Summary"
            variant="outlined"
            required
            hide-details
          />
        </v-row>
        <v-row class="justify-center pa-2" no-gutters>
          <v-file-input
            @keyup.enter="updateRom()"
            label="Custom cover [Coming soon]"
            prepend-inner-icon="mdi-image"
            prepend-icon=""
            variant="outlined"
            disabled
            hide-details
          />
        </v-row>
        <v-row class="justify-center pa-2" no-gutters>
          <v-btn @click="show = false">Cancel</v-btn>
          <v-btn
            @click="updateRom()"
            class="text-rommGreen ml-5"
            >Apply</v-btn
          >
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.edit-content {
  width: 900px;
}

.edit-content-tablet {
  width: 570px;
}

.edit-content-mobile {
  width: 85vw;
}
</style>
