<script setup lang="ts">
import { defineProps } from "vue";
import { TModelPrice } from "@/dto/dto";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const { modelPrice, idx } = defineProps<{
  modelPrice: TModelPrice;
  idx: number;
}>();
</script>

<template>
  <el-descriptions
    :title="t('submit.row_title') + ' #' + (idx + 1)"
    :column="3"
    border
  >
    <el-descriptions-item :label="t('submit.new_model_name')">
      {{ modelPrice.new_model_name }}
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
          >{{ modelPrice.proof_content }}</el-link
        >
      </template>
      <template v-else>
        {{ modelPrice.proof_content }}
      </template>
    </el-descriptions-item>
  </el-descriptions>
</template>
