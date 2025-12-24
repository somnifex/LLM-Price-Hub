<script setup lang="ts">
import { defineProps } from "vue";
import { TModelPrice } from "@/dto/dto";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const { modelPrice, idx, models } = defineProps<{
  modelPrice: TModelPrice;
  idx: number;
  models: Array<{ id: number; name: string; vendor?: string }>;
}>();

const modelDict = models.reduce((acc, model) => {
  acc[model.id] = { ...model };
  return acc;
}, {} as Record<number, { id: number; name: string; vendor?: string }>);

const emits = defineEmits<{
  (e: "edit"): void;
  (e: "remove"): void;
}>();
</script>

<template>
  <el-descriptions
    :title="t('submit.row_title') + ' #' + (idx + 1)"
    :column="3"
    border
  >
    <template #extra>
      <el-button link type="primary" @click="emits('edit')">{{
        t("common.edit")
      }}</el-button>
      <el-button link type="danger" @click="emits('remove')">{{
        t("submit.remove_row")
      }}</el-button>
    </template>
    <el-descriptions-item :label="t('submit.standard_model')">
      {{
        modelPrice.mode === "existing"
          ? modelPrice.standard_model_id
            ? modelDict[modelPrice.standard_model_id].name +
              (modelDict[modelPrice.standard_model_id].vendor
                ? " (" + modelDict[modelPrice.standard_model_id].vendor + ")"
                : "")
            : ""
          : modelPrice.new_model_name
      }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('table.input')">
      {{ modelPrice.price_in }} {{ modelPrice.currency }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('table.cache_hit_input')">
      {{ modelPrice.cache_hit_input_price }} {{ modelPrice.currency }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('admin.provider_model_name')">
      {{ modelPrice.provider_model_name }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('table.output')">
      {{ modelPrice.price_out }} {{ modelPrice.currency }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('table.cache_hit_output')">
      {{ modelPrice.cache_hit_output_price }} {{ modelPrice.currency }}
    </el-descriptions-item>
    <el-descriptions-item :label="t('submit.proof_section')">
      <template v-if="modelPrice.proof_type === 'url'">
        <!-- <a :href="modelPrice.proof_content">{{ modelPrice.proof_content }}</a> -->
        <el-link
          :href="modelPrice.proof_content"
          type="primary"
          target="_blank"
        >
          {{ modelPrice.proof_content }}
        </el-link>
      </template>
      <template v-else>
        {{ modelPrice.proof_content }}
      </template>
    </el-descriptions-item>
  </el-descriptions>
</template>
