<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <div class="page-title">
          Campaign Tracking
          <span v-if="campaignId" class="text-sm text-gray-400 ml-2">
            (Campaign ID: {{ campaignId }})
          </span>
        </div>
        <div class="page-subtitle">{{ trackings.length }} tracking events</div>
      </div>
    </div>

    <div
      class="overflow-x-auto rounded-xl border border-border dark:border-border-dark"
    >
      <table class="w-full text-sm">
        <thead>
          <tr class="bg-surface-off dark:bg-surface-dark-off">
            <th class="th">ID</th>
            <th class="th">Contact ID</th>
            <th class="th">Action</th>
            <th class="th">URL</th>
            <th class="th">IP</th>
            <th class="th">Country</th>
            <th class="th">Browser</th>
            <th class="th">Created At</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!trackings.length">
            <td
              colspan="8"
              class="text-center py-12 text-gray-400 dark:text-gray-600"
            >
              No tracking events for this campaign yet.
            </td>
          </tr>
          <tr
            v-for="t in trackings"
            :key="t.id"
            class="hover:bg-surface-off dark:hover:bg-surface-dark-off border-b border-border dark:border-border-dark last:border-0"
          >
            <td class="td text-gray-500 dark:text-gray-400">
              {{ t.id }}
            </td>
            <td class="td">
              {{ t.contact_id }}
            </td>
            <td class="td">
              <span
                :class="[
                  'badge',
                  t.action_type === 'open' ? 'badge-sent' : 'badge-failed',
                ]"
              >
                {{ t.action_type }}
              </span>
            </td>
            <td class="td max-w-xs truncate">
              <a
                v-if="t.url"
                :href="t.url"
                target="_blank"
                rel="noopener noreferrer"
                class="text-primary hover:underline"
              >
                {{ t.url }}
              </a>
              <span v-else class="text-gray-400 dark:text-gray-600">—</span>
            </td>
            <td class="td text-gray-500 dark:text-gray-400">
              {{ t.address_ip || "—" }}
            </td>
            <td class="td text-gray-500 dark:text-gray-400">
              {{ t.country || "—" }}
            </td>
            <td class="td text-gray-500 dark:text-gray-400 max-w-xs truncate">
              {{ t.browser || "—" }}
            </td>
            <td class="td text-gray-500 dark:text-gray-400">
              {{ formatDate(t.created_at) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();
const route = useRoute();

const campaignId = ref(null);
const trackings = ref([]);

function syncCampaignFromRoute() {
  const raw = route.params.campaign_id || route.params.campaignId;
  const parsed = raw ? Number(raw) : NaN;
  campaignId.value = Number.isNaN(parsed) ? null : parsed;
}

onMounted(() => {
  syncCampaignFromRoute();
  load();
});

watch(
  () => route.params.campaign_id,
  () => {
    syncCampaignFromRoute();
    load();
  },
);

async function load() {
  if (!campaignId.value) {
    trackings.value = [];
    return;
  }
  try {
    const params = new URLSearchParams();
    params.set("actiontype", "list");
    params.set("campaign_id", String(campaignId.value));

    const res = await api.get(`/tracking?${params.toString()}`);
    trackings.value = res.data || [];
  } catch (e) {
    console.error("LOAD TRACKINGS ERROR", e.response || e);
    toast.show("Failed to load campaign tracking events", "error");
    trackings.value = [];
  }
}

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}
</script>

<style scoped>
.th {
  @apply text-left px-4 py-3 text-xs uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400;
}
.td {
  @apply px-4 py-3 align-middle;
}
</style>
