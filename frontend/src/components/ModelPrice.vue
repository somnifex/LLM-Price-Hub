<script setup lang="ts">
import { defineProps, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { TModelPrice } from "@/dto/dto";

const { t } = useI18n();

const props = defineProps<{
  models: Array<{ id: number; name: string; vendor?: string }>;
  currencyOptions: Array<{ label: string; value: string }>;
  value?: TModelPrice | null;
}>();

const emits = defineEmits<{
  (e: "save", priceForm: TModelPrice): void;
}>();

const dialogVisible = ref(false);
const showDialog = () => {
  dialogVisible.value = true;
};
defineExpose({ showDialog });

const emptyForm = (): TModelPrice => ({
  mode: "existing",
  standard_model_id: null,
  new_model_name: "",
  new_model_vendor: "",
  provider_model_name: "",
  price_in: 0,
  price_out: 0,
  cache_hit_input_price: null,
  cache_hit_output_price: null,
  currency: "USD",
  proof_type: "text",
  proof_content: "",
  _id: Date.now(),
});

const priceForm = ref<TModelPrice>(emptyForm());

const onSubmit = () => {
  // Handle form submission logic here
  emits("save", { ...priceForm.value });
  dialogVisible.value = false;
};

watch(
  () => props.value,
  (val: TModelPrice | null | undefined) => {
    if (val) {
      priceForm.value = { ...val };
    } else {
      priceForm.value = emptyForm();
    }
  },
  { immediate: true }
);
</script>
<template>
  <div>
    <!-- ModelPrice component content goes here -->
    <el-dialog
      v-model="dialogVisible"
      destroy-on-close
      @closed="Object.assign(priceForm, emptyForm())"
    >
      <template #header>
        <div class="section-header">
          <h4 class="text-lg font-semibold text-secondary-900">
            {{ t("submit.row_title") }}
          </h4>
        </div>
      </template>
      <el-form label-position="top" class="space-y-8">
        <div class="space-y-4">
          <div class="p-5 space-y-4">
            <el-radio-group
              v-model="priceForm.mode"
              class="bg-gray-50 rounded-xl p-2 border border-gray-100"
            >
              <el-radio value="existing">{{
                t("submit.use_existing_model")
              }}</el-radio>
              <el-radio value="new">{{
                t("submit.request_new_model")
              }}</el-radio>
            </el-radio-group>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <template v-if="priceForm.mode === 'existing'">
                <el-form-item :label="t('submit.select_model')">
                  <el-select
                    v-model="priceForm.standard_model_id"
                    class="w-full"
                    filterable
                  >
                    <el-option
                      v-for="m in props.models"
                      :key="m.id"
                      :label="m.name + (m.vendor ? ' (' + m.vendor + ')' : '')"
                      :value="m.id"
                    />
                  </el-select>
                </el-form-item>
              </template>
              <template v-else>
                <el-form-item :label="t('submit.new_model_name')">
                  <el-input
                    v-model="priceForm.new_model_name"
                    :placeholder="t('submit.new_model_name_placeholder')"
                  />
                </el-form-item>
                <el-form-item :label="t('submit.new_model_vendor')">
                  <el-input
                    v-model="priceForm.new_model_vendor"
                    :placeholder="t('submit.new_model_vendor_placeholder')"
                  />
                </el-form-item>
              </template>
            </div>

            <el-form-item :label="t('submit.provider_model_name')">
              <el-input
                v-model="priceForm.provider_model_name"
                :placeholder="t('submit.provider_model_name_placeholder')"
              />
            </el-form-item>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <el-form-item :label="t('submit.price_in')">
                <el-input-number
                  v-model="priceForm.price_in"
                  :min="0"
                  :step="0.0001"
                  controls-position="right"
                  class="w-full"
                />
              </el-form-item>
              <el-form-item :label="t('submit.price_out')">
                <el-input-number
                  v-model="priceForm.price_out"
                  :min="0"
                  :step="0.0001"
                  controls-position="right"
                  class="w-full"
                />
              </el-form-item>
              <el-form-item :label="t('submit.cache_hit_input')">
                <el-input-number
                  v-model="priceForm.cache_hit_input_price"
                  :min="0"
                  :step="0.0001"
                  controls-position="right"
                  class="w-full"
                />
              </el-form-item>
              <el-form-item :label="t('submit.cache_hit_output')">
                <el-input-number
                  v-model="priceForm.cache_hit_output_price"
                  :min="0"
                  :step="0.0001"
                  controls-position="right"
                  class="w-full"
                />
              </el-form-item>
            </div>

            <el-form-item :label="t('submit.currency')">
              <el-select v-model="priceForm.currency" class="w-full" filterable>
                <el-option
                  v-for="opt in props.currencyOptions"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </el-form-item>

            <el-form-item :label="t('submit.proof_type')">
              <el-radio-group v-model="priceForm.proof_type">
                <el-radio value="text">{{ t("submit.proof_text") }}</el-radio>
                <el-radio value="url">{{ t("submit.proof_url") }}</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="priceForm.proof_content"
                :type="priceForm.proof_type === 'text' ? 'textarea' : 'text'"
                :placeholder="
                  priceForm.proof_type === 'url'
                    ? 'https://example.com/proof'
                    : t('submit.proof_description')
                "
              />
            </el-form-item>
          </div>
        </div>
      </el-form>
      <template #footer>
        <div class="flex justify-end space-x-4">
          <el-button @click="dialogVisible = false">{{
            t("common.cancel")
          }}</el-button>
          <el-button type="primary" @click="onSubmit">{{
            t("common.confirm")
          }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>
