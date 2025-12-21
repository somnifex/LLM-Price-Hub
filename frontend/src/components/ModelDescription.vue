<script setup lang="ts">
import { DefineProps } from "vue";
import { TModelPrice } from "@/dto/dto";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const { modelPrice, idx } = defineProps<{
  modelPrice: TModelPrice;
  idx: number;
}>();
</script>

<template>
  <el-descriptions :title="t('submit.row_title') + ' #' + (idx + 1)">
  </el-descriptions>
</template>
