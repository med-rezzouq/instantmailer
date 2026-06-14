<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">
          Warmup Task Runs
        </h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Task ID: {{ taskId }}
        </p>
      </div>

      <RouterLink
        to="/warmup"
        class="inline-flex items-center rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
      >
        Back to Warmup
      </RouterLink>
    </div>

    <div
      class="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-900"
    >
      <div v-if="loading" class="p-6 text-sm text-gray-500 dark:text-gray-400">
        Loading task runs...
      </div>

      <div v-else-if="error" class="p-6 text-sm text-red-600 dark:text-red-400">
        {{ error }}
      </div>

      <div
        v-else-if="!runs.length"
        class="p-6 text-sm text-gray-500 dark:text-gray-400"
      >
        No warmup runs found for this task.
      </div>

      <div v-else class="overflow-x-auto">
        <table
          class="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-800"
        >
          <thead class="bg-gray-50 dark:bg-gray-800/50">
            <tr>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
              >
                Run ID
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
              >
                Start
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
              >
                Finish
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
              >
                Duration
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
              >
                Status
              </th>
              <th
                class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
              >
                Events
              </th>
            </tr>
          </thead>

          <tbody class="divide-y divide-gray-200 dark:divide-gray-800">
            <template v-for="run in runs" :key="run.rowKey">
              <tr
                class="cursor-pointer transition hover:bg-gray-50 dark:hover:bg-gray-800/40"
                @click="toggleRun(run.rowKey)"
              >
                <td class="px-4 py-4">
                  <div class="flex items-center gap-3">
                    <span
                      class="inline-flex h-6 w-6 items-center justify-center rounded-md border border-gray-300 text-xs text-gray-600 dark:border-gray-700 dark:text-gray-300"
                    >
                      {{ expanded[run.rowKey] ? "−" : "+" }}
                    </span>
                    <div>
                      <div
                        class="font-medium text-gray-900 dark:text-white break-all"
                      >
                        {{ run.runid || "Legacy run without runid" }}
                      </div>
                    </div>
                  </div>
                </td>

                <td class="px-4 py-4 text-gray-700 dark:text-gray-300">
                  {{ formatDateTime(run.started_at) }}
                </td>

                <td class="px-4 py-4 text-gray-700 dark:text-gray-300">
                  {{ formatDateTime(run.finished_at) }}
                </td>

                <td class="px-4 py-4 text-gray-700 dark:text-gray-300">
                  {{ formatDuration(run.duration_seconds) }}
                </td>

                <td class="px-4 py-4">
                  <span
                    class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                    :class="statusClass(run.status)"
                  >
                    {{ run.status || "unknown" }}
                  </span>
                </td>

                <td class="px-4 py-4 text-gray-700 dark:text-gray-300">
                  {{ run.events.length }}
                </td>
              </tr>

              <tr
                v-if="expanded[run.rowKey]"
                class="bg-gray-50/60 dark:bg-gray-800/30"
              >
                <td colspan="6" class="px-4 py-4">
                  <div
                    class="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700"
                  >
                    <table
                      class="min-w-full divide-y divide-gray-200 text-sm dark:divide-gray-700"
                    >
                      <thead class="bg-white dark:bg-gray-900">
                        <tr>
                          <th
                            class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
                          >
                            Event ID
                          </th>
                          <th
                            class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
                          >
                            Action
                          </th>
                          <th
                            class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
                          >
                            Status
                          </th>
                          <th
                            class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
                          >
                            Target
                          </th>
                          <th
                            class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
                          >
                            Created At
                          </th>
                          <th
                            class="px-4 py-3 text-left font-medium text-gray-600 dark:text-gray-300"
                          >
                            Detail
                          </th>
                        </tr>
                      </thead>
                      <tbody
                        class="divide-y divide-gray-200 dark:divide-gray-800 bg-white dark:bg-gray-900"
                      >
                        <tr v-for="event in run.events" :key="event.id">
                          <td
                            class="px-4 py-3 text-gray-700 dark:text-gray-300"
                          >
                            {{ event.id }}
                          </td>
                          <td
                            class="px-4 py-3 text-gray-700 dark:text-gray-300"
                          >
                            {{ event.action || "—" }}
                          </td>
                          <td class="px-4 py-3">
                            <span
                              class="inline-flex rounded-full px-2.5 py-1 text-xs font-medium"
                              :class="statusClass(event.status)"
                            >
                              {{ event.status || "unknown" }}
                            </span>
                          </td>
                          <td
                            class="px-4 py-3 max-w-xs break-all text-gray-700 dark:text-gray-300"
                          >
                            {{ event.target_value || "—" }}
                          </td>
                          <td
                            class="px-4 py-3 text-gray-700 dark:text-gray-300"
                          >
                            {{ formatDateTime(event.created_at) }}
                          </td>
                          <td
                            class="px-4 py-3 max-w-xl break-words text-gray-700 dark:text-gray-300"
                          >
                            {{ event.detail || "—" }}
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, RouterLink } from "vue-router";
import api from "@/api";

const route = useRoute();

const loading = ref(false);
const error = ref("");
const runs = ref([]);
const expanded = ref({});

const taskId = computed(() => route.params.taskid);

function formatDateTime(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function formatDuration(value) {
  if (value == null) return "—";
  const total = Number(value);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;

  if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

function statusClass(status) {
  if (status === "finished") {
    return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300";
  }
  if (status === "running" || status === "started") {
    return "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300";
  }
  if (status === "finished_with_error") {
    return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300";
  }
  return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
}

function toggleRun(key) {
  expanded.value = {
    ...expanded.value,
    [key]: !expanded.value[key],
  };
}

async function loadRuns() {
  loading.value = true;
  error.value = "";

  try {
    const res = await api.get(`/warmup-tasks/taskrun/${taskId.value}`);
    runs.value = (res.data?.runs || []).map((run, index) => ({
      ...run,
      rowKey: run.runid || `legacy-${index}`,
    }));

    expanded.value = {};
  } catch (err) {
    error.value =
      err?.response?.data?.detail || "Failed to load warmup task runs";
    runs.value = [];
  } finally {
    loading.value = false;
  }
}

onMounted(loadRuns);
watch(() => route.params.taskid, loadRuns);
</script>
