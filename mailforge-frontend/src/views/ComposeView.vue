<template>
  <div>
    <!-- Page Header -->
    <div class="mb-6">
      <div class="page-title">Compose Campaign</div>
      <div class="page-subtitle">
        Create a multi-step email sequence with smart follow-ups
      </div>
    </div>

    <!-- Step Indicator -->
    <div class="flex items-center gap-2 mb-6">
      <div
        v-for="(step, i) in wizardSteps"
        :key="i"
        class="flex items-center gap-2"
      >
        <button
          @click="currentWizardStep = i"
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
          {{ step }}
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

    <!-- ── STEP 0: Campaign Details ── -->
    <div v-if="currentWizardStep === 0">
      <div class="grid grid-cols-[1fr_300px] gap-6">
        <div class="card">
          <div class="font-bold text-sm mb-4">Campaign Details</div>
          <div class="mb-4">
            <label class="form-label"
              >Campaign Name <span class="text-red-500">*</span></label
            >
            <input
              v-model="form.name"
              class="form-input"
              placeholder="e.g. Q2 Outreach Campaign"
            />
          </div>
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="form-label"
                >Subject Line <span class="text-red-500">*</span></label
              >
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
          <div class="grid grid-cols-2 gap-4 mb-4">
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

          <!-- Segment Tags -->
          <div class="mb-4">
            <label class="form-label">Segment Tags</label>
            <div class="flex gap-2 flex-wrap mb-2">
              <span
                v-for="tag in form.segment_tags"
                :key="tag"
                class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary dark:bg-primary-dark/20 dark:text-primary-dark border border-primary/20 dark:border-primary-dark/30"
              >
                {{ tag }}
                <button
                  @click="removeTag(tag)"
                  class="hover:text-red-500 transition-colors"
                >
                  <svg
                    class="w-3 h-3"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2.5"
                  >
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </button>
              </span>
            </div>
            <div class="flex gap-2">
              <input
                v-model="tagInput"
                @keydown.enter.prevent="addTag"
                @keydown.comma.prevent="addTag"
                class="form-input flex-1"
                placeholder="Type a tag and press Enter..."
              />
              <button @click="addTag" class="btn btn-ghost btn-sm">Add</button>
            </div>
          </div>
        </div>

        <!-- Right Panel: Provider + Templates -->
        <div>
          <div class="card mb-4">
            <div class="font-bold mb-3 text-sm">Sending Provider</div>
            <div
              class="flex items-center gap-3 p-3 rounded-lg border border-primary/30 bg-primary/5 dark:bg-primary-dark/10 dark:border-primary-dark/30"
            >
              <div
                class="w-8 h-8 rounded-lg bg-primary/10 dark:bg-primary-dark/20 flex items-center justify-center"
              >
                <svg
                  class="w-4 h-4 text-primary dark:text-primary-dark"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div>
                <div class="text-sm font-semibold">PowerMTA</div>
                <div class="text-xs text-gray-500 dark:text-gray-400">
                  High-volume delivery engine
                </div>
              </div>
              <svg
                class="w-4 h-4 text-green-500 ml-auto"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
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

      <div class="flex justify-end mt-4">
        <button
          class="btn btn-primary"
          @click="goToStep(1)"
          :disabled="!form.name || !form.subject"
        >
          Next: Email Body
          <svg
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

    <!-- ── STEP 1: Email Body ── -->
    <div v-if="currentWizardStep === 1">
      <div class="card mb-4">
        <div class="font-bold text-sm mb-4">Initial Email Body</div>
        <!-- Rich Text Toolbar -->
        <div
          class="flex gap-1 p-2 bg-surface-off dark:bg-surface-dark-off border border-border dark:border-border-dark border-b-0 rounded-t-lg flex-wrap"
        >
          <button
            v-for="t in toolbarBtns"
            :key="t.cmd"
            @click="fmt(t.cmd)"
            class="w-7 h-7 flex items-center justify-center rounded text-gray-500 dark:text-gray-400 hover:bg-border dark:hover:bg-border-dark hover:text-gray-900 dark:hover:text-gray-100 text-sm font-bold transition-all"
            :title="t.label"
            v-html="t.icon"
          ></button>
          <div class="w-px bg-border dark:bg-border-dark mx-1"></div>
          <!-- Personalization tokens -->
          <div class="relative" v-click-outside="() => (showTokenMenu = false)">
            <button
              @click="showTokenMenu = !showTokenMenu"
              class="px-2 h-7 flex items-center gap-1 rounded text-xs text-primary dark:text-primary-dark hover:bg-primary/10 dark:hover:bg-primary-dark/10 font-medium transition-all"
            >
              <svg
                class="w-3 h-3"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
              </svg>
              Variables
            </button>
            <div
              v-if="showTokenMenu"
              class="absolute top-8 left-0 z-50 bg-white dark:bg-surface-dark border border-border dark:border-border-dark rounded-lg shadow-lg py-1 w-44"
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
        </div>
        <div
          ref="editor"
          contenteditable="true"
          class="border border-border dark:border-border-dark rounded-b-lg p-4 min-h-[300px] bg-surface-off dark:bg-surface-dark-off focus:outline-none focus:border-primary dark:focus:border-primary-dark"
          style="color: inherit"
        ></div>
      </div>

      <div class="flex justify-between mt-4">
        <button class="btn btn-ghost" @click="goToStep(0)">
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
          Back
        </button>
        <button class="btn btn-primary" @click="goToStep(2)">
          Next: Follow-ups
          <svg
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

    <!-- ── STEP 2: Follow-up Sequence ── -->
    <div v-if="currentWizardStep === 2">
      <!-- Stop Conditions Banner -->
      <div
        class="card mb-4 border-amber-300 dark:border-amber-700 bg-amber-50 dark:bg-amber-900/10"
      >
        <div class="flex items-start gap-3">
          <svg
            class="w-5 h-5 text-amber-500 dark:text-amber-400 mt-0.5 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
            />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div class="flex-1">
            <div
              class="font-semibold text-sm text-amber-800 dark:text-amber-300 mb-2"
            >
              Global Stop Conditions
            </div>
            <div class="text-xs text-amber-700 dark:text-amber-400 mb-3">
              The entire sequence stops immediately when any of these conditions
              are met.
            </div>
            <div class="flex flex-wrap gap-3">
              <label class="flex items-center gap-2 cursor-pointer select-none">
                <div class="relative">
                  <input
                    type="checkbox"
                    v-model="stopConditions.onReply"
                    class="sr-only"
                  />
                  <div
                    :class="[
                      'w-9 h-5 rounded-full transition-colors',
                      stopConditions.onReply
                        ? 'bg-amber-500'
                        : 'bg-gray-300 dark:bg-gray-600',
                    ]"
                  ></div>
                  <div
                    :class="[
                      'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform',
                      stopConditions.onReply ? 'translate-x-4' : '',
                    ]"
                  ></div>
                </div>
                <span
                  class="text-sm font-medium text-amber-800 dark:text-amber-300"
                  >Stop on Reply</span
                >
              </label>
              <label class="flex items-center gap-2 cursor-pointer select-none">
                <div class="relative">
                  <input
                    type="checkbox"
                    v-model="stopConditions.onUnsubscribe"
                    class="sr-only"
                  />
                  <div
                    :class="[
                      'w-9 h-5 rounded-full transition-colors',
                      stopConditions.onUnsubscribe
                        ? 'bg-amber-500'
                        : 'bg-gray-300 dark:bg-gray-600',
                    ]"
                  ></div>
                  <div
                    :class="[
                      'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform',
                      stopConditions.onUnsubscribe ? 'translate-x-4' : '',
                    ]"
                  ></div>
                </div>
                <span
                  class="text-sm font-medium text-amber-800 dark:text-amber-300"
                  >Stop on Unsubscribe</span
                >
              </label>
              <label class="flex items-center gap-2 cursor-pointer select-none">
                <div class="relative">
                  <input
                    type="checkbox"
                    v-model="stopConditions.onBounce"
                    class="sr-only"
                  />
                  <div
                    :class="[
                      'w-9 h-5 rounded-full transition-colors',
                      stopConditions.onBounce
                        ? 'bg-amber-500'
                        : 'bg-gray-300 dark:bg-gray-600',
                    ]"
                  ></div>
                  <div
                    :class="[
                      'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform',
                      stopConditions.onBounce ? 'translate-x-4' : '',
                    ]"
                  ></div>
                </div>
                <span
                  class="text-sm font-medium text-amber-800 dark:text-amber-300"
                  >Stop on Bounce</span
                >
              </label>
              <label class="flex items-center gap-2 cursor-pointer select-none">
                <div class="relative">
                  <input
                    type="checkbox"
                    v-model="stopConditions.onClick"
                    class="sr-only"
                  />
                  <div
                    :class="[
                      'w-9 h-5 rounded-full transition-colors',
                      stopConditions.onClick
                        ? 'bg-amber-500'
                        : 'bg-gray-300 dark:bg-gray-600',
                    ]"
                  ></div>
                  <div
                    :class="[
                      'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform',
                      stopConditions.onClick ? 'translate-x-4' : '',
                    ]"
                  ></div>
                </div>
                <span
                  class="text-sm font-medium text-amber-800 dark:text-amber-300"
                  >Stop on Link Click</span
                >
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Initial Email Preview Card -->
      <div class="relative mb-4">
        <div
          class="card border-l-4 border-l-primary dark:border-l-primary-dark opacity-80"
        >
          <div class="flex items-center gap-3">
            <div
              class="w-8 h-8 rounded-full bg-primary/10 dark:bg-primary-dark/20 flex items-center justify-center shrink-0"
            >
              <span
                class="text-xs font-bold text-primary dark:text-primary-dark"
                >1</span
              >
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold truncate">Initial Email</div>
              <div class="text-xs text-gray-500 dark:text-gray-400 truncate">
                Subject: {{ form.subject || "(no subject)" }}
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span
                class="text-xs text-gray-400 bg-surface-off dark:bg-surface-dark-off px-2 py-1 rounded"
                >Sends immediately</span
              >
              <span
                class="text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded font-medium"
                >Initial</span
              >
            </div>
          </div>
        </div>
        <!-- Connector line -->
        <div
          v-if="followups.length"
          class="absolute left-8 -bottom-4 w-px h-4 bg-border dark:bg-border-dark ml-3"
        ></div>
      </div>

      <!-- Follow-up Steps -->
      <div v-for="(fu, idx) in followups" :key="fu.id" class="relative mb-4">
        <!-- Connector from previous -->
        <div
          class="absolute left-8 -top-4 w-px h-4 bg-border dark:bg-border-dark ml-3"
        ></div>

        <div
          :class="[
            'card border-l-4 transition-all',
            expandedFollowup === idx
              ? 'border-l-blue-500 dark:border-l-blue-400'
              : 'border-l-gray-200 dark:border-l-gray-700',
          ]"
        >
          <!-- Follow-up Header -->
          <div
            class="flex items-center gap-3 cursor-pointer"
            @click="toggleFollowup(idx)"
          >
            <div
              class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0"
            >
              <span
                class="text-xs font-bold text-blue-600 dark:text-blue-400"
                >{{ idx + 2 }}</span
              >
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-semibold truncate">
                Follow-up #{{ idx + 1 }}
                <span
                  v-if="fu.subject"
                  class="font-normal text-gray-500 dark:text-gray-400"
                >
                  — {{ fu.subject }}</span
                >
              </div>
              <div class="flex items-center gap-2 mt-0.5">
                <svg
                  class="w-3 h-3 text-gray-400"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 6v6l4 2" />
                </svg>
                <span class="text-xs text-gray-500 dark:text-gray-400">
                  Wait {{ fu.delay_value }} {{ fu.delay_unit }} after
                  {{ idx === 0 ? "initial email" : "follow-up #" + idx }}
                </span>
                <span
                  v-if="fu.stop_on_reply"
                  class="text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-1.5 py-0.5 rounded"
                >
                  ⛔ Stops if replied
                </span>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button
                @click.stop="removeFollowup(idx)"
                class="w-7 h-7 flex items-center justify-center rounded text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
                title="Remove follow-up"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M3 6h18M19 6l-1 14H6L5 6M10 11v6M14 11v6M9 6V4h6v2"
                  />
                </svg>
              </button>
              <svg
                :class="[
                  'w-4 h-4 text-gray-400 transition-transform',
                  expandedFollowup === idx ? 'rotate-180' : '',
                ]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </div>
          </div>

          <!-- Expanded Follow-up Editor -->
          <div
            v-if="expandedFollowup === idx"
            class="mt-4 border-t border-border dark:border-border-dark pt-4"
          >
            <div class="grid grid-cols-3 gap-4 mb-4">
              <!-- Delay -->
              <div>
                <label class="form-label">Wait Before Sending</label>
                <div class="flex gap-2">
                  <input
                    v-model.number="fu.delay_value"
                    type="number"
                    min="1"
                    class="form-input w-20"
                    placeholder="3"
                  />
                  <select v-model="fu.delay_unit" class="form-input flex-1">
                    <option value="hours">Hours</option>
                    <option value="days">Days</option>
                    <option value="weeks">Weeks</option>
                  </select>
                </div>
              </div>
              <!-- Subject -->
              <div>
                <label class="form-label">Subject Line</label>
                <input
                  v-model="fu.subject"
                  class="form-input"
                  :placeholder="'Re: ' + (form.subject || 'your subject')"
                />
              </div>
              <!-- Stop on Reply override -->
              <div>
                <label class="form-label">Step Stop Condition</label>
                <label
                  class="flex items-center gap-2 mt-2 cursor-pointer select-none"
                >
                  <div class="relative">
                    <input
                      type="checkbox"
                      v-model="fu.stop_on_reply"
                      class="sr-only"
                    />
                    <div
                      :class="[
                        'w-9 h-5 rounded-full transition-colors',
                        fu.stop_on_reply
                          ? 'bg-blue-500'
                          : 'bg-gray-300 dark:bg-gray-600',
                      ]"
                    ></div>
                    <div
                      :class="[
                        'absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform',
                        fu.stop_on_reply ? 'translate-x-4' : '',
                      ]"
                    ></div>
                  </div>
                  <span class="text-sm text-gray-600 dark:text-gray-400"
                    >Skip if replied</span
                  >
                </label>
              </div>
            </div>

            <!-- Follow-up body editor -->
            <label class="form-label">Email Body</label>
            <div
              class="flex gap-1 p-2 bg-surface-off dark:bg-surface-dark-off border border-border dark:border-border-dark border-b-0 rounded-t-lg flex-wrap"
            >
              <button
                v-for="t in toolbarBtns"
                :key="t.cmd"
                @click="fmtFollowup(idx, t.cmd)"
                class="w-7 h-7 flex items-center justify-center rounded text-gray-500 dark:text-gray-400 hover:bg-border dark:hover:bg-border-dark hover:text-gray-900 dark:hover:text-gray-100 text-sm font-bold transition-all"
                :title="t.label"
                v-html="t.icon"
              ></button>
            </div>
            <div
              :ref="(el) => setFollowupEditorRef(el, idx)"
              contenteditable="true"
              class="border border-border dark:border-border-dark rounded-b-lg p-4 min-h-[160px] bg-surface-off dark:bg-surface-dark-off focus:outline-none focus:border-primary dark:focus:border-primary-dark"
              style="color: inherit"
              @input="syncFollowupBody(idx)"
            ></div>
          </div>
        </div>

        <!-- Connector line to next -->
        <div
          v-if="idx < followups.length - 1"
          class="absolute left-8 -bottom-4 w-px h-4 bg-border dark:bg-border-dark ml-3"
        ></div>
      </div>

      <!-- Add Follow-up Button -->
      <div class="flex items-center gap-4 my-6">
        <div class="flex-1 h-px bg-border dark:bg-border-dark"></div>
        <button
          @click="addFollowup"
          class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 border-dashed border-border dark:border-border-dark text-sm text-gray-500 dark:text-gray-400 hover:border-primary dark:hover:border-primary-dark hover:text-primary dark:hover:text-primary-dark transition-all"
        >
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v8M8 12h8" />
          </svg>
          Add Follow-up Step
        </button>
        <div class="flex-1 h-px bg-border dark:bg-border-dark"></div>
      </div>

      <!-- Sequence Summary -->
      <div
        v-if="followups.length"
        class="card bg-surface-off dark:bg-surface-dark-off mb-4"
      >
        <div class="font-bold text-sm mb-3">Sequence Summary</div>
        <div class="grid grid-cols-3 gap-4 text-center">
          <div>
            <div class="text-2xl font-bold text-primary dark:text-primary-dark">
              {{ followups.length + 1 }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              Total Emails
            </div>
          </div>
          <div>
            <div class="text-2xl font-bold text-blue-500">
              {{ totalSequenceDays }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              Days Span
            </div>
          </div>
          <div>
            <div class="text-2xl font-bold text-amber-500">
              {{ activeStopConditionsCount }}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              Stop Conditions
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-between">
        <button class="btn btn-ghost" @click="goToStep(1)">
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
          Back
        </button>
        <button class="btn btn-primary" @click="goToStep(3)">
          Next: Review & Send
          <svg
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

    <!-- ── STEP 3: Review & Send ── -->
    <div v-if="currentWizardStep === 3">
      <div class="grid grid-cols-[1fr_300px] gap-6">
        <div>
          <!-- Campaign Summary Card -->
          <div class="card mb-4">
            <div class="font-bold text-sm mb-4">Campaign Overview</div>
            <div class="grid grid-cols-2 gap-3">
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
                  Provider
                </div>
                <div class="text-sm font-semibold flex items-center gap-1.5">
                  <svg
                    class="w-3.5 h-3.5 text-primary dark:text-primary-dark"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  PowerMTA
                </div>
              </div>
              <div
                class="p-3 rounded-lg bg-surface-off dark:bg-surface-dark-off"
              >
                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Segments
                </div>
                <div class="text-sm font-semibold">
                  <span v-if="!form.segment_tags.length" class="text-gray-400"
                    >All contacts</span
                  >
                  <span v-else>{{ form.segment_tags.join(", ") }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Sequence Timeline Review -->
          <div class="card mb-4">
            <div class="font-bold text-sm mb-4">Email Sequence Timeline</div>
            <div class="space-y-3">
              <!-- Initial -->
              <div class="flex items-start gap-3">
                <div class="flex flex-col items-center">
                  <div
                    class="w-8 h-8 rounded-full bg-primary/10 dark:bg-primary-dark/20 flex items-center justify-center text-xs font-bold text-primary dark:text-primary-dark"
                  >
                    1
                  </div>
                  <div
                    v-if="followups.length"
                    class="w-px flex-1 bg-border dark:bg-border-dark mt-1 min-h-[20px]"
                  ></div>
                </div>
                <div class="flex-1 pb-3">
                  <div class="text-sm font-semibold">Initial Email</div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    {{ form.subject }}
                  </div>
                  <div
                    class="text-xs text-green-600 dark:text-green-400 mt-0.5"
                  >
                    Sends immediately on launch
                  </div>
                </div>
              </div>
              <!-- Follow-ups -->
              <div
                v-for="(fu, idx) in followups"
                :key="fu.id"
                class="flex items-start gap-3"
              >
                <div class="flex flex-col items-center">
                  <div
                    class="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-xs font-bold text-blue-600 dark:text-blue-400"
                  >
                    {{ idx + 2 }}
                  </div>
                  <div
                    v-if="idx < followups.length - 1"
                    class="w-px flex-1 bg-border dark:bg-border-dark mt-1 min-h-[20px]"
                  ></div>
                </div>
                <div class="flex-1 pb-3">
                  <div class="text-sm font-semibold">
                    Follow-up #{{ idx + 1 }}
                  </div>
                  <div class="text-xs text-gray-500 dark:text-gray-400">
                    {{ fu.subject || "Re: " + form.subject }}
                  </div>
                  <div class="flex items-center gap-2 mt-0.5">
                    <span class="text-xs text-blue-600 dark:text-blue-400"
                      >⏱ +{{ fu.delay_value }} {{ fu.delay_unit }}</span
                    >
                    <span
                      v-if="fu.stop_on_reply || stopConditions.onReply"
                      class="text-xs text-amber-600 dark:text-amber-400"
                      >⛔ Stops on reply</span
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Stop Conditions Review -->
          <div class="card mb-4">
            <div class="font-bold text-sm mb-3">Active Stop Conditions</div>
            <div class="flex flex-wrap gap-2">
              <span
                v-if="stopConditions.onReply"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
              >
                <svg
                  class="w-3 h-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M9 17H5a2 2 0 01-2-2V5a2 2 0 012-2h11a2 2 0 012 2v3"
                  />
                  <path
                    d="M13 21l9-9-9-9v5a16 16 0 00-9 9h5z"
                    transform="scale(-1,1) translate(-24,0)"
                  />
                </svg>
                Stop on Reply
              </span>
              <span
                v-if="stopConditions.onUnsubscribe"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
              >
                <svg
                  class="w-3 h-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M23 11l-4 4-2-2" />
                </svg>
                Stop on Unsubscribe
              </span>
              <span
                v-if="stopConditions.onBounce"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
              >
                <svg
                  class="w-3 h-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                Stop on Bounce
              </span>
              <span
                v-if="stopConditions.onClick"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
              >
                <svg
                  class="w-3 h-3"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5" />
                </svg>
                Stop on Click
              </span>
              <span
                v-if="!activeStopConditionsCount"
                class="text-sm text-gray-400 dark:text-gray-600 italic"
                >No stop conditions set — sequence runs to completion</span
              >
            </div>
          </div>
        </div>

        <!-- Right Panel: Send / Save -->
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
              <svg
                v-if="saving"
                class="animate-spin w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              <svg
                v-else
                class="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v14a2 2 0 01-2 2z"
                />
                <path d="M17 21v-8H7v8M7 3v5h8" />
              </svg>
              Save Draft
            </button>

            <button
              v-if="sendMode === 'now'"
              class="btn btn-primary w-full"
              @click="sendNow"
              :disabled="sending"
            >
              <svg
                v-if="sending"
                class="animate-spin w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M21 12a9 9 0 1 1-6.219-8.56" />
              </svg>
              <svg
                v-else
                class="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M22 2L11 13" />
                <path d="M22 2L15 22l-4-9-9-4 20-7z" />
              </svg>
              {{ sending ? "Launching..." : "Launch Campaign" }}
            </button>
          </div>

          <div class="card">
            <div class="font-bold text-sm mb-3">Pre-send Checklist</div>
            <div class="space-y-2">
              <div
                v-for="check in preflightChecks"
                :key="check.id"
                class="flex items-center gap-2 text-sm"
              >
                <svg
                  v-if="check.passed"
                  class="w-4 h-4 text-green-500 shrink-0"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <svg
                  v-else
                  class="w-4 h-4 text-red-400 shrink-0"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <circle cx="12" cy="12" r="10" />
                  <path d="M15 9l-6 6M9 9l6 6" />
                </svg>
                <span
                  :class="
                    check.passed
                      ? 'text-gray-600 dark:text-gray-400'
                      : 'text-red-500'
                  "
                  >{{ check.label }}</span
                >
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-between mt-4">
        <button class="btn btn-ghost" @click="goToStep(2)">
          <svg
            class="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
          Back
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/api";
import { useToastStore } from "@/stores/toast";

const toast = useToastStore();
const router = useRouter();
const route = useRoute();

// ── State ──────────────────────────────────────────────────────────────
const currentWizardStep = ref(0);
const wizardSteps = [
  "Campaign Details",
  "Email Body",
  "Follow-ups",
  "Review & Send",
];

const editor = ref(null);
const saving = ref(false);
const sending = ref(false);
const templates = ref([]);
const tagInput = ref("");
const showTokenMenu = ref(false);
const expandedFollowup = ref(null);
const sendMode = ref("now");
const followupEditorRefs = ref({});

const form = ref({
  name: "",
  subject: "",
  preview_text: "",
  from_name: "",
  reply_to: "",
  provider: "powermta",
  segment_tags: [],
});

const stopConditions = ref({
  onReply: true,
  onUnsubscribe: true,
  onBounce: true,
  onClick: false,
});

const followups = ref([]);

// ── Toolbar & Tokens ──────────────────────────────────────────────────
const toolbarBtns = [
  { cmd: "bold", label: "Bold", icon: "<b>B</b>" },
  { cmd: "italic", label: "Italic", icon: "<i>I</i>" },
  { cmd: "underline", label: "Underline", icon: "<u>U</u>" },
  { cmd: "insertUnorderedList", label: "Bullet List", icon: "<span>≡</span>" },
  { cmd: "insertOrderedList", label: "Numbered List", icon: "<span>1.</span>" },
];

const personalizationTokens = [
  { value: "{{first_name}}", label: "First name" },
  { value: "{{last_name}}", label: "Last name" },
  { value: "{{email}}", label: "Email" },
  { value: "{{company}}", label: "Company" },
  { value: "{{unsubscribe_url}}", label: "Unsubscribe" },
];

// ── Computed ──────────────────────────────────────────────────────────
const totalSequenceDays = computed(() => {
  return followups.value.reduce((acc, fu) => {
    const v = fu.delay_value || 0;
    if (fu.delay_unit === "hours") return acc + v / 24;
    if (fu.delay_unit === "weeks") return acc + v * 7;
    return acc + v;
  }, 0);
});

const activeStopConditionsCount = computed(() => {
  return Object.values(stopConditions.value).filter(Boolean).length;
});

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
    passed: followups.value.every((f) => f.delay_value > 0),
  },
]);

// ── Lifecycle ─────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    templates.value = (await api.get("/templates?limit=20")).data;
  } catch (_) {}
  if (route.query.template && editor.value) {
    editor.value.innerHTML = route.query.template;
  }
});

// ── Methods ───────────────────────────────────────────────────────────
function goToStep(n) {
  currentWizardStep.value = n;
}

function fmt(cmd) {
  document.execCommand(cmd, false, null);
  editor.value?.focus();
}

function fmtFollowup(idx, cmd) {
  document.execCommand(cmd, false, null);
  followupEditorRefs.value[idx]?.focus();
}

function setFollowupEditorRef(el, idx) {
  if (el) followupEditorRefs.value[idx] = el;
}

function syncFollowupBody(idx) {
  followups.value[idx].html_body =
    followupEditorRefs.value[idx]?.innerHTML || "";
}

function insertToken(token) {
  editor.value?.focus();
  document.execCommand("insertText", false, token);
  showTokenMenu.value = false;
}

function loadTemplate(t) {
  if (editor.value) editor.value.innerHTML = t.html_content;
  toast.show("Template loaded", "success");
}

function addTag() {
  const tag = tagInput.value.trim().replace(/,$/, "");
  if (tag && !form.value.segment_tags.includes(tag)) {
    form.value.segment_tags.push(tag);
  }
  tagInput.value = "";
}

function removeTag(tag) {
  form.value.segment_tags = form.value.segment_tags.filter((t) => t !== tag);
}

function addFollowup() {
  const id = Date.now();
  followups.value.push({
    id,
    subject: "",
    delay_value: 3,
    delay_unit: "days",
    stop_on_reply: stopConditions.value.onReply,
    html_body: "",
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

function buildPayload() {
  return {
    ...form.value,
    html_content: editor.value?.innerHTML || "<p></p>",
    stop_on_reply: stopConditions.value.onReply,
    stop_on_unsubscribe: stopConditions.value.onUnsubscribe,
    stop_on_bounce: stopConditions.value.onBounce,
    stop_on_click: stopConditions.value.onClick,
    followups: followups.value.map((fu) => ({
      subject: fu.subject || "Re: " + form.value.subject,
      delay_value: fu.delay_value,
      delay_unit: fu.delay_unit,
      stop_on_reply: fu.stop_on_reply,
      html_body: fu.html_body || "<p></p>",
    })),
  };
}

async function saveDraft() {
  saving.value = true;
  try {
    await api.post("/campaigns", buildPayload());
    toast.show("Draft saved!", "success");
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  } finally {
    saving.value = false;
  }
}

async function sendNow() {
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
  )
    return;

  sending.value = true;
  try {
    const campaign = (await api.post("/campaigns", buildPayload())).data;
    await api.post(`/campaigns/${campaign.id}/send`);
    toast.show("🚀 Campaign launched!", "success");
    router.push("/campaigns");
  } catch (e) {
    toast.show(e.response?.data?.detail || e.message, "error");
  } finally {
    sending.value = false;
  }
}
</script>
