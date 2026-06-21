<template>
  <div>
    <div class="mb-6">
      <div class="page-title">
        {{ isEditMode ? "Edit Campaign" : "Compose Campaign" }}
      </div>
      <div class="page-subtitle">
        Create a multi-step email sequence with smart follow-ups
      </div>
    </div>

    <div class="flex items-center gap-2 mb-6 flex-wrap">
      <div
        v-for="(step, i) in wizardSteps"
        :key="i"
        class="flex items-center gap-2"
      >
        <button
          type="button"
          @click="goToStep(i)"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all border',
            currentWizardStep === i
              ? 'bg-primary text-white border-primary dark:bg-primary-dark dark:border-primary-dark'
              : currentWizardStep > i
                ? 'bg-green-100 text-green-700 border-green-300 dark:bg-green-900/30 dark:text-green-400 dark:border-green-700'
                : 'bg-surface-off text-gray-500 border-border dark:bg-surface-dark-off dark:border-border-dark dark:text-gray-400',
          ]"
        >
          <span
            :class="[
              'w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold',
              currentWizardStep === i
                ? 'bg-white/30'
                : currentWizardStep > i
                  ? 'bg-green-500 text-white'
                  : 'bg-border dark:bg-border-dark',
            ]"
          >
            <svg
              v-if="currentWizardStep > i"
              class="w-3 h-3"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
            >
              <path d="M20 6L9 17l-5-5" />
            </svg>
            <span v-else>{{ i + 1 }}</span>
          </span>
          <span>{{ step }}</span>
        </button>

        <svg
          v-if="i < wizardSteps.length - 1"
          class="w-4 h-4 text-gray-300 dark:text-gray-600"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M9 18l6-6-6-6" />
        </svg>
      </div>
    </div>

    <div v-if="currentWizardStep === 0">
      <div class="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-6">
        <div class="card">
          <div class="font-bold text-sm mb-4">Campaign Details</div>

          <div class="mb-4">
            <label class="form-label">
              Campaign Name <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.name"
              class="form-input"
              placeholder="e.g. Q2 Outreach Campaign"
            />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="form-label">
                Subject Line <span class="text-red-500">*</span>
              </label>
              <input
                v-model="form.subject"
                class="form-input"
                placeholder="Your email subject..."
              />
            </div>

            <div>
              <label class="form-label">Preview Text</label>
              <input
                v-model="form.preview_text"
                class="form-input"
                placeholder="Short preview shown in inbox..."
              />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="form-label">From Name</label>
              <input
                v-model="form.from_name"
                class="form-input"
                placeholder="John from Acme"
              />
            </div>

            <div>
              <label class="form-label">Reply-To Email</label>
              <input
                v-model="form.reply_to"
                class="form-input"
                placeholder="replies@yourdomain.com"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="form-label">
                Contact Group <span class="text-red-500">*</span>
              </label>
              <select
                :value="form.group_id ?? ''"
                @change="onGroupChange"
                class="form-input"
                :class="{ 'border-red-500 focus:border-red-500': groupError }"
              >
                <option value="" disabled>Select a contact group...</option>
                <option
                  v-for="group in contactGroups"
                  :key="group.id"
                  :value="group.id"
                >
                  {{ group.name }}
                </option>
              </select>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Choose which contact group this campaign should target.
              </p>
              <p v-if="groupError" class="text-xs text-red-500 mt-1">
                {{ groupError }}
              </p>
            </div>

            <div>
              <label class="form-label">General Warm-up Delay</label>
              <div class="flex gap-2">
                <input
                  v-model.number="form.general_warmup_delay_value"
                  type="number"
                  min="0"
                  class="form-input w-24"
                  placeholder="10"
                />
                <select
                  v-model="form.general_warmup_delay_unit"
                  class="form-input flex-1"
                >
                  <option value="seconds">Seconds</option>
                  <option value="minutes">Minutes</option>
                  <option value="hours">Hours</option>
                </select>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Minimum time between any two emails sent to the same contact in
                this campaign.
              </p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label class="form-label">Max Bounces</label>
              <input
                v-model.number="form.max_bounces"
                type="number"
                min="0"
                class="form-input"
                placeholder="0"
              />
            </div>

            <div>
              <label class="form-label">Max Unsubscribes</label>
              <input
                v-model.number="form.max_unsubscribes"
                type="number"
                min="0"
                class="form-input"
                placeholder="0"
              />
            </div>

            <div>
              <label class="form-label">Max Reports</label>
              <input
                v-model.number="form.max_complaints"
                type="number"
                min="0"
                class="form-input"
                placeholder="0"
              />
            </div>

            <div>
              <label class="form-label">Max Follow-ups per sequence</label>
              <input
                v-model.number="form.max_followups"
                type="number"
                min="0"
                class="form-input"
                placeholder="e.g. 3"
              />
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Limits how many follow-up emails are sent before/after a reply
                in this campaign. Leave empty for unlimited.
              </p>
            </div>
          </div>

          <div class="mb-4">
            <label class="form-label">Labels / Segments</label>

            <Multiselect
              v-model="selectedLabels"
              mode="tags"
              :options="mergedLabelOptions"
              :searchable="true"
              :filter-results="false"
              :min-chars="1"
              :resolve-on-load="true"
              :delay="0"
              :close-on-select="false"
              :clear-on-select="false"
              :hide-selected="false"
              :create-option="true"
              :loading="labelsLoading"
              valueProp="id"
              label="name"
              trackBy="name"
              disabledProp="disabled"
              placeholder="Type to search labels..."
              noOptionsText="Start typing to search labels"
              noResultsText="No matching labels found"
              @search-change="searchLabels"
              @create="handleCreateLabel"
            />

            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Search existing labels from the database and select multiple.
              Press Enter to create a new one if no match exists.
            </p>
          </div>

          <div class="flex justify-end mt-4">
            <button
              class="btn btn-primary"
              @click="goToStep(1)"
              :disabled="!form.name || !form.subject || autosaving"
            >
              <svg
                v-if="autosaving"
                class="animate-spin w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              <span>{{ autosaving ? "Saving..." : "Next Email Body" }}</span>
              <svg
                v-if="!autosaving"
                class="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M9 18l6-6-6-6" />
              </svg>
            </button>
          </div>
        </div>

        <div>
          <div class="card mb-4">
            <div class="font-bold mb-3 text-sm">Sending Provider</div>

            <div class="mb-3">
              <label class="form-label">SMTP Provider</label>
              <select v-model.number="form.provider_id" class="form-input">
                <option :value="null">Select a provider...</option>
                <option
                  v-for="p in availableProviders"
                  :key="p.id"
                  :value="p.id"
                >
                  {{ p.name || p.label || p.host }}
                </option>
              </select>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Emails will be sent from the From email configured on this SMTP.
              </p>
            </div>
          </div>

          <div class="card">
            <div class="font-bold mb-3 text-sm">Quick Templates</div>
            <div
              v-if="!templates.length"
              class="text-sm text-gray-400 dark:text-gray-600"
            >
              No templates yet
            </div>
            <button
              v-for="t in templates"
              :key="t.id"
              class="btn btn-ghost btn-sm w-full justify-start mb-2 text-left"
              @click="loadTemplate(t)"
            >
              <svg
                class="w-3.5 h-3.5 shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <path d="M3 9h18M9 21V9" />
              </svg>
              <span class="truncate">{{ t.name }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="currentWizardStep === 1">
      <div class="card mb-4">
        <div class="font-bold text-sm mb-4">Initial Email Body</div>

        <div
          class="relative flex gap-1 p-2 bg-surface-off dark:bg-surface-dark-off border border-border dark:border-border-dark border-b-0 rounded-t-lg flex-wrap"
        >
          <button
            v-for="t in toolbarBtns"
            :key="t.cmd"
            @click="fmt(t.cmd)"
            class="w-7 h-7 flex items-center justify-center rounded text-gray-500 dark:text-gray-400 hover:bg-border dark:hover:bg-border-dark hover:text-gray-900 dark:hover:text-gray-100 text-sm font-bold transition-all"
            :title="t.label"
            v-html="t.icon"
          />
          <div class="w-px bg-border dark:bg-border-dark mx-1"></div>

          <button
            type="button"
            @click="showTokenMenu = !showTokenMenu"
            class="px-2 h-7 flex items-center gap-1 rounded text-xs text-primary dark:text-primary-dark hover:bg-primary/10 dark:hover:bg-primary-dark/10 font-medium transition-all"
          >
            Variables
          </button>

          <div
            v-if="showTokenMenu"
            class="absolute z-50 mt-8 bg-white dark:bg-surface-dark border border-border dark:border-border-dark rounded-lg shadow-lg py-1 w-44"
          >
            <button
              v-for="token in personalizationTokens"
              :key="token.value"
              @click="insertToken(token.value)"
              class="w-full text-left px-3 py-1.5 text-xs hover:bg-surface-off dark:hover:bg-surface-dark-off transition-colors"
            >
              <span class="font-mono text-primary dark:text-primary-dark">{{
                token.value
              }}</span>
              <span class="text-gray-400 ml-2">{{ token.label }}</span>
            </button>
          </div>
        </div>

        <div
          ref="editor"
          contenteditable="true"
          class="border border-border dark:border-border-dark rounded-b-lg p-4 min-h-[300px] bg-surface-off dark:bg-surface-dark-off focus:outline-none focus:border-primary dark:focus:border-primary-dark"
          style="color: inherit"
          @input="initialHtmlBody = $event.target.innerHTML"
        ></div>

        <div class="flex justify-between mt-4">
          <button class="btn btn-ghost" @click="goToStep(0)">Back</button>
          <button
            class="btn btn-primary"
            @click="goToStep(2)"
            :disabled="autosaving"
          >
            <svg
              v-if="autosaving"
              class="animate-spin w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
            <span>{{ autosaving ? "Saving..." : "Next Follow-ups" }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="currentWizardStep === 2">
      <div v-for="(fu, idx) in followups" :key="fu.id" class="card mb-4">
        <div class="flex items-center justify-between mb-4">
          <div class="font-semibold">
            {{
              fu.is_reply_sequence
                ? `Reply Sequence ${idx + 1}`
                : `Follow-up ${idx + 1}`
            }}
          </div>
          <button
            type="button"
            class="text-red-500 text-sm"
            @click="removeFollowup(idx)"
          >
            Remove
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label class="form-label">Wait after sending this sequence</label>
            <div class="flex gap-2">
              <input
                v-model.number="fu.delayvalue"
                type="number"
                min="0"
                class="form-input w-24"
              />
              <select v-model="fu.delayunit" class="form-input flex-1">
                <option value="seconds">Seconds</option>
                <option value="minutes">Minutes</option>
                <option value="hours">Hours</option>
              </select>
            </div>
          </div>

          <div>
            <label class="form-label">Subject Line</label>
            <input
              v-model="fu.subject"
              class="form-input"
              :placeholder="`Re: ${form.subject || 'your subject'}`"
            />
          </div>

          <div>
            <label class="form-label">Step Stop Condition</label>
            <label class="flex items-center gap-2 mt-2">
              <input type="checkbox" v-model="fu.stoponreply" />
              <span>Skip if replied</span>
            </label>
          </div>
        </div>

        <div class="mb-4">
          <label class="flex items-center gap-2">
            <input type="checkbox" v-model="fu.is_reply_sequence" />
            <span>This is a reply sequence</span>
          </label>
        </div>

        <div
          v-if="fu.is_reply_sequence"
          class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4"
        >
          <div>
            <label class="form-label">Wait after last contact reply</label>
            <div class="flex gap-2">
              <input
                v-model.number="fu.wait_after_contact_reply_value"
                type="number"
                min="0"
                class="form-input w-24"
              />
              <select
                v-model="fu.wait_after_contact_reply_unit"
                class="form-input flex-1"
              >
                <option value="seconds">Seconds</option>
                <option value="minutes">Minutes</option>
                <option value="hours">Hours</option>
              </select>
            </div>
          </div>
        </div>

        <label class="form-label">Email Body</label>
        <div
          :ref="(el) => setFollowupEditorRef(el, idx)"
          contenteditable="true"
          class="border border-border dark:border-border-dark rounded-lg p-4 min-h-[160px] bg-surface-off dark:bg-surface-dark-off focus:outline-none focus:border-primary dark:focus:border-primary-dark"
          style="color: inherit"
          @input="syncFollowupBody(idx)"
        ></div>
      </div>

      <div class="flex justify-center my-6">
        <button
          type="button"
          @click="addFollowup"
          class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-dashed border-border dark:border-border-dark text-sm text-gray-500 dark:text-gray-400 hover:border-primary dark:hover:border-primary-dark hover:text-primary dark:hover:text-primary-dark transition-all"
        >
          Add Follow-up Step
        </button>
      </div>

      <div class="flex justify-between">
        <button class="btn btn-ghost" @click="goToStep(1)">Back</button>
        <button
          class="btn btn-primary"
          @click="goToStep(3)"
          :disabled="autosaving"
        >
          <svg
            v-if="autosaving"
            class="animate-spin w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
          <span>{{ autosaving ? "Saving..." : "Next Review & Send" }}</span>
        </button>
      </div>
    </div>

    <div v-if="currentWizardStep === 3">
      <div class="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-6">
        <div>
          <div class="card mb-4">
            <div class="font-bold text-sm mb-4">Campaign Overview</div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Campaign Name
                </div>
                <div class="text-sm font-semibold">{{ form.name }}</div>
              </div>

              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Subject Line
                </div>
                <div class="text-sm font-semibold truncate">
                  {{ form.subject }}
                </div>
              </div>

              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Contact Group
                </div>
                <div class="text-sm font-semibold">
                  {{ selectedGroupName }}
                </div>
              </div>

              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  General Warm-up Delay
                </div>
                <div class="text-sm font-semibold">
                  {{ form.general_warmup_delay_value }}
                  {{ form.general_warmup_delay_unit }}
                </div>
              </div>

              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Max Bounces
                </div>
                <div class="text-sm font-semibold">{{ form.max_bounces }}</div>
              </div>

              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Max Unsubscribes
                </div>
                <div class="text-sm font-semibold">
                  {{ form.max_unsubscribes }}
                </div>
              </div>

              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Max Reports
                </div>
                <div class="text-sm font-semibold">
                  {{ form.max_complaints }}
                </div>
              </div>

              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off md:col-span-2"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Labels
                </div>
                <div class="text-sm font-semibold">
                  <span v-if="!form.segment_tags.length" class="text-gray-400">
                    All contacts
                  </span>
                  <span v-else>{{ form.segment_tags.join(", ") }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <div class="card mb-4">
            <div class="font-bold text-sm mb-4">Launch Campaign</div>
            <div class="space-y-3 mb-4">
              <label
                class="flex items-center gap-3 cursor-pointer p-2 rounded-lg hover:bg-surface-off dark:hover:bg-surface-dark-off transition-colors"
              >
                <input
                  type="radio"
                  v-model="sendMode"
                  value="now"
                  class="text-primary"
                />
                <div>
                  <div class="text-sm font-medium">Send Now</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    Launch immediately
                  </div>
                </div>
              </label>

              <label
                class="flex items-center gap-3 cursor-pointer p-2 rounded-lg hover:bg-surface-off dark:hover:bg-surface-dark-off transition-colors"
              >
                <input
                  type="radio"
                  v-model="sendMode"
                  value="draft"
                  class="text-primary"
                />
                <div>
                  <div class="text-sm font-medium">Save as Draft</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    Configure and send later
                  </div>
                </div>
              </label>
            </div>

            <button
              v-if="sendMode === 'draft'"
              class="btn btn-ghost w-full mb-2"
              @click="saveDraft"
              :disabled="saving"
            >
              {{
                saving
                  ? "Saving..."
                  : isEditMode
                    ? "Update Campaign"
                    : "Save Draft"
              }}
            </button>

            <button
              v-if="sendMode === 'ready'"
              class="btn btn-primary w-full mb-2"
              @click="markReady"
              :disabled="saving"
            >
              {{ saving ? "Saving..." : "Mark as Ready" }}
            </button>

            <button
              v-if="sendMode === 'now'"
              class="btn btn-primary w-full"
              @click="sendNow"
              :disabled="sending"
            >
              {{ sending ? "Launching..." : "Launch Campaign" }}
            </button>
          </div>
        </div>
      </div>

      <div class="flex justify-between mt-4">
        <button class="btn btn-ghost" @click="goToStep(2)">Back</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import Multiselect from "@vueform/multiselect";
import "@vueform/multiselect/themes/default.css";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();
const router = useRouter();
const route = useRoute();

const currentWizardStep = ref(0);
const wizardSteps = [
  "Campaign Details",
  "Email Body",
  "Follow-ups",
  "Review & Send",
];

const editor = ref(null);
const initialHtmlBody = ref("<p></p>");
const saving = ref(false);
const sending = ref(false);
const templates = ref([]);
const showTokenMenu = ref(false);
const expandedFollowup = ref(null);
const sendMode = ref("now");
const followupEditorRefs = ref([]);
const isEditMode = computed(() => !!route.params.id);
const autosaving = computed(() => saving.value);

const availableProviders = ref([]);
const contactGroups = ref([]);
const selectedLabels = ref([]);
const labelOptions = ref([]);
const labelsLoading = ref(false);
const selectedLabelObjects = ref([]);
const groupError = ref("");

let labelsSearchTimeout = null;
let latestLabelsQuery = "";

const form = ref({
  name: "",
  subject: "",
  preview_text: "",
  from_name: "",
  reply_to: "",
  provider_id: null,
  group_id: null,
  segment_tags: [],
  max_bounces: 0,
  max_unsubscribes: 0,
  max_complaints: 0,
  general_warmup_delay_value: 10,
  general_warmup_delay_unit: "minutes",
  max_followups: null,
});

const stopConditions = ref({
  onReply: true,
  onUnsubscribe: true,
  onBounce: true,
  onClick: false,
});

const followups = ref([]);

const toolbarBtns = [
  { cmd: "bold", label: "Bold", icon: "<b>B</b>" },
  { cmd: "italic", label: "Italic", icon: "<i>I</i>" },
  { cmd: "underline", label: "Underline", icon: "<u>U</u>" },
  {
    cmd: "insertUnorderedList",
    label: "Bullet List",
    icon: "<span>• •</span>",
  },
  {
    cmd: "insertOrderedList",
    label: "Numbered List",
    icon: "<span>1.</span>",
  },
];

const personalizationTokens = [
  { value: "{{firstname}}", label: "First name" },
  { value: "{{lastname}}", label: "Last name" },
  { value: "{{email}}", label: "Email" },
  { value: "{{company}}", label: "Company" },
  { value: "{{unsubscribeurl}}", label: "Unsubscribe" },
];

const totalSequenceHours = computed(() =>
  followups.value.reduce((acc, fu) => {
    const v = Number(fu.delayvalue || 0);
    if (fu.delayunit === "seconds") return acc + v / 3600;
    if (fu.delayunit === "minutes") return acc + v / 60;
    return acc + v;
  }, 0),
);

const activeStopConditionsCount = computed(
  () => Object.values(stopConditions.value).filter(Boolean).length,
);

const preflightChecks = computed(() => [
  { id: "name", label: "Campaign name set", passed: !!form.value.name },
  { id: "subject", label: "Subject line set", passed: !!form.value.subject },
  {
    id: "body",
    label: "Email body not empty",
    passed: !!editor.value?.innerHTML?.trim(),
  },
  { id: "segs", label: "Segment or all contacts", passed: true },
  {
    id: "delay",
    label: "Follow-up delays valid",
    passed: followups.value.every((f) => Number(f.delayvalue) >= 0),
  },
]);

const selectedGroupName = computed(() => {
  if (form.value.group_id == null) return "All Contacts";
  const group = contactGroups.value.find(
    (g) => Number(g.id) === Number(form.value.group_id),
  );
  return group?.name || "Selected group";
});

const mergedLabelOptions = computed(() => {
  const map = new Map();
  const selectedIds = new Set(
    (selectedLabels.value || []).map((v) => String(v)),
  );

  [...labelOptions.value, ...selectedLabelObjects.value].forEach((item) => {
    if (!item) return;
    const key = String(item.id ?? item.name);

    if (!map.has(key)) {
      map.set(key, {
        ...item,
        disabled: selectedIds.has(String(item.id)),
      });
    }
  });

  return Array.from(map.values());
});

watch(
  selectedLabels,
  (vals) => {
    const optionMap = new Map(
      mergedLabelOptions.value.map((item) => [String(item.id), item]),
    );

    const resolved = (vals || [])
      .map((v) => {
        if (v && typeof v === "object") return v;
        return optionMap.get(String(v)) || null;
      })
      .filter(Boolean);

    form.value.segment_tags = resolved
      .map((item) => item?.name?.trim())
      .filter(Boolean);
  },
  { deep: true },
);

onMounted(async () => {
  try {
    const templatesRes = await api.get("/templates?limit=20");
    templates.value = templatesRes.data || [];
  } catch {}

  try {
    const providersRes = await api.get("/smtp");
    availableProviders.value = providersRes.data || [];
  } catch (e) {
    console.error("Failed to load SMTP providers", e);
  }

  try {
    const labelsRes = await api.get("/labels", { params: { limit: 20 } });
    labelOptions.value = labelsRes.data || [];
  } catch (e) {
    console.error("Failed to load labels", e);
  }

  await loadContactGroups();
  await nextTick();

  if (route.query.template && editor.value) {
    editor.value.innerHTML = route.query.template;
    initialHtmlBody.value = editor.value.innerHTML;
  }

  if (route.params.id) {
    await loadCampaign(route.params.id);
  }
});

function validateGroupSelection() {
  if (form.value.group_id == null) {
    groupError.value = "Please select a contact group";
    return false;
  }
  groupError.value = "";
  return true;
}

async function loadContactGroups() {
  try {
    const { data } = await api.get("/contacts/groups");
    contactGroups.value = data || [];
  } catch (e) {
    console.error("Failed to load contact groups", e);
    contactGroups.value = [];
  }
}

function onGroupChange(event) {
  const value = event.target.value;
  form.value.group_id = value === "" ? null : Number(value);

  if (form.value.group_id != null) {
    groupError.value = "";
  }
}
async function searchLabels(query) {
  latestLabelsQuery = query || "";

  if (labelsSearchTimeout) {
    clearTimeout(labelsSearchTimeout);
  }

  if (!latestLabelsQuery.trim()) {
    try {
      const { data } = await api.get("/labels", { params: { limit: 20 } });
      labelOptions.value = data || [];
    } catch {
      labelOptions.value = [];
    }
    return;
  }

  labelsLoading.value = true;

  labelsSearchTimeout = setTimeout(async () => {
    try {
      const { data } = await api.get("/labels", {
        params: {
          q: latestLabelsQuery,
          limit: 20,
        },
      });

      labelOptions.value = data || [];
    } catch (e) {
      console.error("Failed to search labels", e);
      labelOptions.value = [];
    } finally {
      labelsLoading.value = false;
    }
  }, 250);
}

async function handleCreateLabel(newLabelName) {
  const name = String(newLabelName || "").trim();
  if (!name) return;

  const existing = mergedLabelOptions.value.find(
    (item) => item.name?.trim().toLowerCase() === name.toLowerCase(),
  );

  if (existing) {
    const existsInSelected = (selectedLabels.value || []).some(
      (item) => String(item) === String(existing.id),
    );
    if (!existsInSelected) {
      selectedLabels.value = [...selectedLabels.value, existing.id];
    }
    return;
  }

  try {
    const { data } = await api.post("/labels", {
      name,
      description: null,
    });

    labelOptions.value = [data, ...labelOptions.value];
    selectedLabelObjects.value = [data, ...selectedLabelObjects.value];
    selectedLabels.value = [...selectedLabels.value, data.id];
    toast.show("Label created", "success");
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

async function goToStep(n) {
  currentWizardStep.value = n;
  await nextTick();

  if (n === 1 && editor.value) {
    editor.value.innerHTML = initialHtmlBody.value || "<p></p>";
  }

  if (n === 2) {
    followupEditorRefs.value.forEach((el, idx) => {
      if (el && followups.value[idx]) {
        el.innerHTML = followups.value[idx].htmlbody || "<p></p>";
      }
    });
  }
}

function fmt(cmd) {
  editor.value?.focus();
  document.execCommand(cmd, false, null);
}

function fmtFollowup(idx, cmd) {
  followupEditorRefs.value[idx]?.focus();
  document.execCommand(cmd, false, null);
}

function setFollowupEditorRef(el, idx) {
  if (el) followupEditorRefs.value[idx] = el;
}

function syncFollowupBody(idx) {
  if (followups.value[idx]) {
    followups.value[idx].htmlbody =
      followupEditorRefs.value[idx]?.innerHTML || "<p></p>";
  }
}

function insertToken(token) {
  editor.value?.focus();
  document.execCommand("insertText", false, token);
  showTokenMenu.value = false;
}

function loadTemplate(t) {
  const html = t.html_content || t.htmlcontent || "<p></p>";
  initialHtmlBody.value = html;
  if (editor.value) editor.value.innerHTML = html;
  toast.show("Template loaded", "success");
}

function addFollowup() {
  const id = Date.now();
  followups.value.push({
    id,
    subject: "",
    delayvalue: 10,
    delayunit: "minutes",
    stoponreply: stopConditions.value.onReply,
    htmlbody: "<p></p>",
    is_reply_sequence: false,
    wait_after_contact_reply_value: 10,
    wait_after_contact_reply_unit: "minutes",
  });
  expandedFollowup.value = followups.value.length - 1;
}

function removeFollowup(idx) {
  followups.value.splice(idx, 1);
  if (expandedFollowup.value === idx) expandedFollowup.value = null;
}

function toggleFollowup(idx) {
  expandedFollowup.value = expandedFollowup.value === idx ? null : idx;
}

function fillFormFromCampaign(campaign) {
  const orderedSteps = [...(campaign.steps || [])].sort(
    (a, b) => a.step_number - b.step_number,
  );

  const initialStep =
    orderedSteps.find((s) => s.step_type === "initial") ||
    orderedSteps[0] ||
    null;

  const followupSteps = orderedSteps.filter((s) => s.step_type !== "initial");

  form.value = {
    name: campaign.name || "",
    subject: campaign.subject || initialStep?.subject || "",
    preview_text: campaign.preview_text || "",
    from_name: campaign.from_name || "",
    reply_to: campaign.reply_to || "",
    provider_id: campaign.provider_id ?? null,
    group_id: campaign.group_id ?? null,
    segment_tags: campaign.segment_tags || [],
    max_bounces: campaign.max_bounces ?? 0,
    max_unsubscribes: campaign.max_unsubscribes ?? 0,
    max_complaints: campaign.max_complaints ?? 0,
    general_warmup_delay_value: campaign.general_warmup_delay_value ?? 10,
    general_warmup_delay_unit: campaign.general_warmup_delay_unit || "minutes",
    max_followups: campaign.max_followups ?? null,
  };

  const byName = new Map(
    (labelOptions.value || []).map((item) => [
      item.name?.trim().toLowerCase(),
      item,
    ]),
  );

  selectedLabelObjects.value = (campaign.segment_tags || []).map((tag, idx) => {
    const normalized = String(tag || "")
      .trim()
      .toLowerCase();
    const existing = byName.get(normalized);

    if (existing) {
      return existing;
    }

    return {
      id: `missing-${idx}-${tag}`,
      name: tag,
    };
  });

  selectedLabels.value = selectedLabelObjects.value.map((item) => item.id);

  const html = initialStep?.html_body || campaign.html_content || "<p></p>";
  initialHtmlBody.value = html;

  followups.value = followupSteps.map((step, i) => ({
    id: step.id || Date.now() + i,
    subject: step.subject || "",
    delayvalue: step.delay_value ?? 10,
    delayunit: step.delay_unit || "minutes",
    stoponreply: !!step.stop_on_reply,
    htmlbody: step.html_body || "<p></p>",
    is_reply_sequence: step.step_type === "reply",
    wait_after_contact_reply_value: step.wait_after_contact_reply_value ?? 10,
    wait_after_contact_reply_unit:
      step.wait_after_contact_reply_unit || "minutes",
  }));

  stopConditions.value = {
    onReply: followups.value.every((f) => f.stoponreply !== false),
    onUnsubscribe: true,
    onBounce: true,
    onClick: false,
  };

  nextTick(() => {
    if (editor.value) {
      editor.value.innerHTML = initialHtmlBody.value || "<p></p>";
    }

    followupEditorRefs.value = [];

    nextTick(() => {
      followupEditorRefs.value.forEach((el, idx) => {
        if (el && followups.value[idx]) {
          el.innerHTML = followups.value[idx].htmlbody || "<p></p>";
        }
      });
    });
  });
}

async function loadCampaign(id) {
  try {
    const { data } = await api.get(`/campaigns/${id}`);
    fillFormFromCampaign(data);
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  }
}

function buildPayload() {
  const steps = [
    {
      step_number: 1,
      step_type: "initial",
      name: "Initial Email",
      subject: form.value.subject,
      html_body: editor.value?.innerHTML || initialHtmlBody.value || "<p></p>",
      plain_body: null,
      delay_value: 0,
      delay_unit: "minutes",
      delay_from: "most_recent",
      stop_on_reply: true,
      is_active: true,
    },
    ...followups.value.map((fu, idx) => {
      const isReply = fu.is_reply_sequence;
      const stopOnReply = !!fu.stoponreply;

      let step_type;
      if (isReply) {
        step_type = "reply";
      } else if (!isReply && stopOnReply) {
        step_type = "followup";
      } else {
        step_type = "post_reply_followup";
      }

      let delay_from;
      if (step_type === "reply") {
        delay_from = "their_reply";
      } else if (step_type === "post_reply_followup") {
        delay_from = "our_reply";
      } else {
        delay_from = "previous_step";
      }

      return {
        step_number: idx + 2,
        step_type,
        name:
          step_type === "reply"
            ? `Reply Sequence ${idx + 1}`
            : step_type === "post_reply_followup"
              ? `Post-reply Follow-up ${idx + 1}`
              : `Follow-up ${idx + 1}`,
        subject: fu.subject || `Re: ${form.value.subject}`,
        html_body:
          followupEditorRefs.value[idx]?.innerHTML || fu.htmlbody || "<p></p>",
        plain_body: null,
        delay_value: Number(fu.delayvalue || 0),
        delay_unit: fu.delayunit || "minutes",
        delay_from,
        stop_on_reply: stopOnReply,
        is_active: true,
        wait_after_contact_reply_value: isReply
          ? Number(fu.wait_after_contact_reply_value || 0)
          : null,
        wait_after_contact_reply_unit: isReply
          ? fu.wait_after_contact_reply_unit || "minutes"
          : null,
      };
    }),
  ];

  let status = null;
  if (sendMode.value === "draft") {
    status = "draft";
  } else if (sendMode.value === "scheduled") {
    status = "scheduled";
  }

  return {
    name: form.value.name,
    subject: form.value.subject,
    preview_text: form.value.preview_text,
    from_name: form.value.from_name,
    reply_to: form.value.reply_to,
    provider_id: form.value.provider_id,
    group_id: form.value.group_id,
    segment_tags: form.value.segment_tags,
    track_opens: true,
    track_clicks: true,
    is_followup: false,
    parent_campaign_id: null,
    scheduled_at: null,
    max_bounces: Number(form.value.max_bounces || 0),
    max_complaints: Number(form.value.max_complaints || 0),
    max_unsubscribes: Number(form.value.max_unsubscribes || 0),
    general_warmup_delay_value: Number(
      form.value.general_warmup_delay_value || 0,
    ),
    general_warmup_delay_unit:
      form.value.general_warmup_delay_unit || "minutes",
    max_followups:
      form.value.max_followups === null || form.value.max_followups === ""
        ? null
        : Number(form.value.max_followups),
    status,
    steps,
  };
}

async function saveDraft() {
  if (!validateGroupSelection()) {
    currentWizardStep.value = 0;
    toast.show("Please select a contact group", "error");
    return;
  }

  saving.value = true;
  try {
    const payload = buildPayload();

    if (payload.status == null) {
      delete payload.status;
    }

    if (route.params.id) {
      await api.put(`/campaigns/${route.params.id}`, payload);
    } else {
      await api.post("/campaigns", payload);
    }

    toast.show("Draft saved!", "success");
    router.push("/campaigns");
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  } finally {
    saving.value = false;
  }
}

async function sendNow() {
  if (!validateGroupSelection()) {
    currentWizardStep.value = 0;
    toast.show("Please select a contact group", "error");
    return;
  }

  if (!form.value.name) {
    toast.show("Campaign name is required", "error");
    return;
  }

  if (!form.value.subject) {
    toast.show("Subject line is required", "error");
    return;
  }

  if (
    !confirm(
      `Launch "${form.value.name}" with ${followups.value.length + 1} emails?`,
    )
  ) {
    return;
  }

  sending.value = true;
  try {
    const payload = buildPayload();

    if (payload.status == null) {
      delete payload.status;
    }

    const campaign = route.params.id
      ? (await api.put(`/campaigns/${route.params.id}`, payload)).data
      : (await api.post("/campaigns", payload)).data;

    await api.post(`/campaigns/${campaign.id}/send`);
    toast.show("Campaign launched!", "success");
    router.push("/campaigns");
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  } finally {
    sending.value = false;
  }
}

async function markReady() {
  if (!validateGroupSelection()) {
    currentWizardStep.value = 0;
    toast.show("Please select a contact group", "error");
    return;
  }

  saving.value = true;
  try {
    const payload = buildPayload();
    payload.status = "ready";

    let campaign;
    if (route.params.id) {
      campaign = (await api.put(`/campaigns/${route.params.id}`, payload)).data;
    } else {
      campaign = (await api.post("/campaigns", payload)).data;
    }

    toast.show("Campaign marked as ready!", "success");
    router.push(`/campaigns/${campaign.id}`);
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  } finally {
    saving.value = false;
  }
}
</script>
