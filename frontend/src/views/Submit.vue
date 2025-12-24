<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import api from "@/api";
import { useI18n } from "vue-i18n";
import { useSettingsStore } from "@/stores/settings";

import { TModelPrice } from "@/dto/dto";
import ModelPrice from "@/components/ModelPrice.vue";
import ModelDescription from "@/components/ModelDescription.vue";

const { t } = useI18n();
const router = useRouter();
const settingsStore = useSettingsStore();

// Data
const models = ref<Array<{ id: number; name: string; vendor?: string }>>([]);
const providers = ref<Array<{ id: number; name: string; status?: string }>>([]);
const loading = ref(false);

// Provider form
const providerMode = ref<"existing" | "new">("existing");
const formProvider = ref({
  provider_id: null as number | null,
  provider_name: "",
  provider_website: "",
  openai_base_url: "",
  gemini_base_url: "",
  claude_base_url: "",
  submit_provider_for_review: false,
  provider_proof_type: "text",
  provider_proof_content: "",
});

// Model price rows
const priceRows = ref<TModelPrice[]>([]);
const concurrentRow = ref<TModelPrice | null>(null);

const modelPriceDialogRef = ref<{ showDialog: () => void } | null>(null);

const currencyOptions = computed(() => {
  const list = settingsStore.currencies;
  if (!list || !list.length) {
    return [
      { label: "USD", value: "USD" },
      { label: "CNY", value: "CNY" },
      { label: "EUR", value: "EUR" },
    ];
  }
  const commons = list.filter((c: any) => c.is_common);
  const rest = list.filter((c: any) => !c.is_common);
  const ordered = [...commons, ...rest];
  return ordered.map((c: any) => {
    const flag = c.flag ? `${c.flag} ` : "";
    return { label: `${flag}${c.code}`, value: c.code };
  });
});

const addRow = () => {
  concurrentRow.value = null;
  console.log(concurrentRow.value);
  modelPriceDialogRef.value?.showDialog();
};

const editRow = (modelPrice: TModelPrice) => {
  concurrentRow.value = { ...modelPrice };
  modelPriceDialogRef.value?.showDialog();
};

const handleEmit = (priceForm: TModelPrice) => {
  if (concurrentRow.value) {
    // Edit existing row
    const idx = priceRows.value.findIndex(
      (r) => r._id === concurrentRow.value!._id
    );
    if (idx !== -1) {
      priceRows.value[idx] = priceForm;
    }
  } else {
    // Add new row
    priceRows.value.push(priceForm);
  }
};

const removeRow = (idx: number) => {
  if (priceRows.value.length === 1) return;
  priceRows.value.splice(idx, 1);
};

const fetchModels = async () => {
  try {
    const res = await api.get("/prices/models");
    models.value = res.data;
  } catch {
    // Silent fail
  }
};

const fetchProviders = async () => {
  try {
    // Get public providers + user's own providers
    const [publicRes, userRes] = await Promise.all([
      api.get("/config/providers"),
      api.get("/user/providers").catch(() => ({ data: [] })),
    ]);
    providers.value = Array.from(
      new Map(
        [...publicRes.data, ...userRes.data].map((item) => [item.id, item])
      ).values()
    );
  } catch {
    // Silent fail
  }
};

const submit = async () => {
  // Provider validation
  if (providerMode.value === "existing" && !formProvider.value.provider_id) {
    ElMessage.error(t("submit.select_provider_error"));
    return;
  }
  if (providerMode.value === "new" && !formProvider.value.provider_name) {
    ElMessage.error(t("submit.enter_provider_name"));
    return;
  }

  // Rows validation
  for (const row of priceRows.value) {
    if (row.mode === "existing" && !row.standard_model_id) {
      ElMessage.error(t("submit.select_model_error"));
      return;
    }
    if (row.mode === "new" && !row.new_model_name) {
      ElMessage.error(t("submit.enter_model_name"));
      return;
    }
    if (!row.proof_content) {
      ElMessage.error(t("submit.proof_required"));
      return;
    }
  }

  loading.value = true;
  try {
    const payload = {
      provider_id:
        providerMode.value === "existing"
          ? formProvider.value.provider_id
          : null,
      provider_name:
        providerMode.value === "new"
          ? formProvider.value.provider_name
          : undefined,
      provider_website: formProvider.value.provider_website,
      openai_base_url: formProvider.value.openai_base_url,
      gemini_base_url: formProvider.value.gemini_base_url,
      claude_base_url: formProvider.value.claude_base_url,
      submit_provider_for_review: formProvider.value.submit_provider_for_review,
      provider_proof_type: formProvider.value.provider_proof_type,
      provider_proof_content: formProvider.value.provider_proof_content,
      prices: priceRows.value.map((r) => ({
        standard_model_id: r.mode === "existing" ? r.standard_model_id : null,
        new_model_name: r.mode === "new" ? r.new_model_name : null,
        new_model_vendor: r.mode === "new" ? r.new_model_vendor : null,
        provider_model_name: r.provider_model_name,
        price_in: r.price_in,
        price_out: r.price_out,
        cache_hit_input_price: r.cache_hit_input_price,
        cache_hit_output_price: r.cache_hit_output_price,
        currency: r.currency,
        proof_type: r.proof_type,
        proof_content: r.proof_content,
      })),
    };

    await api.post("/prices/submit-batch", payload);
    ElMessage.success(t("submit.success"));
    router.push("/admin");
  } catch (e: any) {
    const msg = e?.response?.data?.detail || t("submit.failed");
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
};

onMounted(async () => {
  await settingsStore.fetchCurrencies();
  await settingsStore.fetchUserSettings();
  // Update existing rows to default currency if available
  const def = settingsStore.userSettings.default_currency || "USD";
  priceRows.value = priceRows.value.map((r) => ({ ...r, currency: def }));
  fetchModels();
  fetchProviders();
});
</script>

<template>
  <div class="page-shell">
    <div class="page-hero p-6 md:p-8">
      <div class="section-header">
        <div>
          <p class="section-kicker mb-1">{{ t("submit.title") }}</p>
          <h1 class="text-3xl font-bold text-secondary-900">
            {{ t("submit.provider_section") }}
          </h1>
          <p class="muted-subtitle">{{ t("home.subtitle") }}</p>
        </div>
        <!-- <div class="action-row">
          <el-button type="primary" plain @click="addModelPrice">
            {{ t("submit.add_row") }}
          </el-button>
        </div> -->
      </div>
      <div class="flex flex-wrap gap-3 text-sm text-secondary-700">
        <span
          class="px-3 py-1 rounded-full bg-white/70 border border-primary-100 shadow-sm"
        >
          {{ providers.length }} {{ t("submit.use_existing_provider") }}
        </span>
        <span
          class="px-3 py-1 rounded-full bg-white/70 border border-primary-100 shadow-sm"
        >
          {{ priceRows.length }} {{ t("submit.row_title") }}
        </span>
      </div>
    </div>

    <div class="card-muted p-6 space-y-8 bg-white/90">
      <el-form label-position="top" class="space-y-8">
        <!-- Provider Section -->
        <div class="space-y-4">
          <div class="section-header">
            <div>
              <p class="section-kicker mb-1">
                {{ t("submit.provider_section") }}
              </p>
              <h3 class="text-xl font-semibold text-secondary-900">
                {{ t("submit.provider_section") }}
              </h3>
              <p class="muted-subtitle">
                {{ t("submit.provider_name_placeholder") }}
              </p>
            </div>
            <el-radio-group
              v-model="providerMode"
              class="bg-gray-50 rounded-xl p-2 border border-gray-100"
            >
              <el-radio value="existing">{{
                t("submit.use_existing_provider")
              }}</el-radio>
              <el-radio value="new">{{
                t("submit.create_new_provider")
              }}</el-radio>
            </el-radio-group>
          </div>

          <template v-if="providerMode === 'existing'">
            <el-form-item :label="t('submit.select_provider')">
              <el-select
                v-model="formProvider.provider_id"
                class="w-full"
                filterable
              >
                <el-option
                  v-for="p in providers"
                  :key="p.id"
                  :label="p.name"
                  :value="p.id"
                />
              </el-select>
            </el-form-item>
          </template>
          <template v-else>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <el-form-item :label="t('submit.provider_name')">
                <el-input
                  v-model="formProvider.provider_name"
                  :placeholder="t('submit.provider_name_placeholder')"
                />
              </el-form-item>
              <el-form-item :label="t('submit.provider_website')">
                <el-input
                  v-model="formProvider.provider_website"
                  placeholder="https://example.com"
                />
              </el-form-item>
            </div>

            <el-collapse class="mb-2">
              <el-collapse-item :title="t('submit.api_base_urls')">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <el-form-item label="OpenAI Base URL">
                    <el-input
                      v-model="formProvider.openai_base_url"
                      placeholder="https://api.openai.com/v1"
                    />
                  </el-form-item>
                  <el-form-item label="Gemini Base URL">
                    <el-input v-model="formProvider.gemini_base_url" />
                  </el-form-item>
                  <el-form-item label="Claude Base URL">
                    <el-input v-model="formProvider.claude_base_url" />
                  </el-form-item>
                </div>
              </el-collapse-item>
            </el-collapse>

            <div
              class="card-muted p-4 space-y-3 bg-primary-50/40 border border-primary-100"
            >
              <div class="flex items-center justify-between">
                <p class="text-sm font-semibold text-secondary-800">
                  {{ t("submit.submit_provider_public") }}
                </p>
                <el-switch v-model="formProvider.submit_provider_for_review" />
              </div>

              <template v-if="formProvider.submit_provider_for_review">
                <el-form-item :label="t('submit.provider_proof')">
                  <el-radio-group v-model="formProvider.provider_proof_type">
                    <el-radio value="text">{{
                      t("submit.proof_text")
                    }}</el-radio>
                    <el-radio value="url">{{ t("submit.proof_url") }}</el-radio>
                  </el-radio-group>
                </el-form-item>
                <el-form-item>
                  <el-input
                    v-model="formProvider.provider_proof_content"
                    :type="
                      formProvider.provider_proof_type === 'text'
                        ? 'textarea'
                        : 'text'
                    "
                    :placeholder="
                      formProvider.provider_proof_type === 'url'
                        ? 'https://docs.example.com/pricing'
                        : t('submit.proof_description')
                    "
                  />
                </el-form-item>
              </template>
            </div>
          </template>
        </div>

        <!-- Model Price Rows -->
        <div class="space-y-4">
          <div class="section-header">
            <div>
              <p class="section-kicker mb-1">{{ t("submit.row_title") }}</p>
              <h3 class="text-xl font-semibold text-secondary-900">
                {{ t("submit.price_in") }} / {{ t("submit.price_out") }}
              </h3>
              <p class="muted-subtitle">{{ t("submit.request_new_model") }}</p>
            </div>
            <el-button type="primary" plain @click="addRow">{{
              t("submit.add_row")
            }}</el-button>
          </div>

          <model-price
            ref="modelPriceDialogRef"
            :models="models"
            :currency-options="currencyOptions"
            :value="concurrentRow"
            @save="handleEmit"
          />

          <div
            v-for="(row, idx) in priceRows"
            :key="idx"
            class="card-muted p-5 space-y-4 border border-gray-100 bg-white/80"
          >
            <model-description
              :model-price="row"
              :idx="idx"
              :models="models"
              @edit="editRow(row)"
              @remove="removeRow(idx)"
            />
          </div>
        </div>

        <div class="action-row pt-4 border-t border-dashed border-gray-200">
          <el-button @click="router.back()">{{
            t("submit.cancel_btn")
          }}</el-button>
          <el-button type="primary" :loading="loading" @click="submit">{{
            t("submit.submit_btn")
          }}</el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>
