<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-[#171614] p-4">
    <div class="w-full max-w-[440px] bg-surface dark:bg-surface-dark border border-border dark:border-border-dark rounded-2xl p-10 shadow-lg">
      <div class="flex items-center justify-center gap-3 mb-8">
        <svg class="w-8 h-8" viewBox="0 0 32 32" fill="none"><rect width="32" height="32" rx="8" fill="#01696f"/><path d="M6 10L16 18L26 10" stroke="white" stroke-width="2" stroke-linecap="round"/><path d="M6 10H26V23C26 23.55 25.55 24 25 24H7C6.45 24 6 23.55 6 23V10Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span class="font-display font-extrabold text-xl tracking-tight">MailForge</span>
      </div>

      <!-- LOGIN -->
      <div v-if="mode==='login'">
        <h1 class="text-lg font-bold text-center mb-1">Welcome back</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 text-center mb-8">Sign in to your account to continue</p>
        <div v-if="error" class="bg-danger-light dark:bg-danger/20 text-danger dark:text-danger-dark border border-danger/30 rounded-lg p-3 text-sm mb-4">{{ error }}</div>
        <div class="mb-5"><label class="form-label">Email</label><input v-model="email" class="form-input" type="email" placeholder="you@company.com" @keydown.enter="submit"></div>
        <div class="mb-6"><label class="form-label">Password</label><input v-model="password" class="form-input" type="password" placeholder="••••••••" @keydown.enter="submit"></div>
        <button class="btn btn-primary w-full justify-center" :disabled="loading" @click="submit">
          <svg v-if="loading" class="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          {{ loading ? 'Signing in...' : 'Sign in' }}
        </button>
        <p class="text-center text-sm text-gray-500 dark:text-gray-400 mt-6">Don't have an account? <a class="text-primary dark:text-primary-dark font-semibold cursor-pointer" @click="mode='register'">Create one</a></p>
      </div>

      <!-- REGISTER -->
      <div v-else>
        <h1 class="text-lg font-bold text-center mb-1">Create account</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 text-center mb-8">Start sending campaigns in minutes</p>
        <div v-if="error" class="bg-danger-light dark:bg-danger/20 text-danger dark:text-danger-dark border border-danger/30 rounded-lg p-3 text-sm mb-4">{{ error }}</div>
        <div class="mb-4"><label class="form-label">Full name</label><input v-model="name" class="form-input" placeholder="Your Name"></div>
        <div class="mb-4"><label class="form-label">Email</label><input v-model="email" class="form-input" type="email" placeholder="you@company.com"></div>
        <div class="mb-6"><label class="form-label">Password</label><input v-model="password" class="form-input" type="password" placeholder="Min 8 characters" @keydown.enter="submit"></div>
        <button class="btn btn-primary w-full justify-center" :disabled="loading" @click="submit">
          {{ loading ? 'Creating...' : 'Create account' }}
        </button>
        <p class="text-center text-sm text-gray-500 dark:text-gray-400 mt-6">Already have an account? <a class="text-primary dark:text-primary-dark font-semibold cursor-pointer" @click="mode='login'">Sign in</a></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const mode = ref('login')
const email = ref(''); const password = ref(''); const name = ref('')
const loading = ref(false); const error = ref('')

async function submit() {
  error.value = ''; loading.value = true
  try {
    if (mode.value === 'login') await auth.login(email.value, password.value)
    else await auth.register(name.value, email.value, password.value)
    router.push('/dashboard')
  } catch(e) {
    error.value = e.response?.data?.detail || e.message || 'Authentication failed'
  } finally { loading.value = false }
}
</script>
