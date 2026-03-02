<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useData } from "vitepress";

const props = defineProps<{
  chart: string;
  caption?: string;
}>();

const { isDark } = useData();
const container = ref<HTMLElement | null>(null);

const renderDiagram = async () => {
  if (!container.value || !props.chart.trim()) {
    return;
  }

  const { default: mermaid } = await import("mermaid");
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "loose",
    theme: isDark.value ? "dark" : "default",
  });

  const diagramId = `mermaid-${Math.random().toString(36).slice(2, 10)}`;
  const { svg, bindFunctions } = await mermaid.render(diagramId, props.chart.trim());

  if (!container.value) {
    return;
  }

  container.value.innerHTML = svg;
  bindFunctions?.(container.value);
};

onMounted(() => {
  void renderDiagram();
  watch([() => props.chart, isDark], () => {
    void renderDiagram();
  });
});
</script>

<template>
  <figure class="mermaid-diagram">
    <div ref="container" class="mermaid-diagram__canvas" />
    <figcaption v-if="caption">{{ caption }}</figcaption>
  </figure>
</template>
