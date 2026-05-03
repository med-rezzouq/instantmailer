# MailForge Frontend — Vue 3 + Tailwind CSS

## Setup

```bash
npm install
npm run dev
```

App runs at http://localhost:3000

## Key improvements over the old HTML file

- ✅ Tokens persisted in localStorage via Pinia — no more logout on refresh
- ✅ Proper Vue Router navigation guards
- ✅ Auto token refresh on 401
- ✅ Component-based architecture
- ✅ Dark/light mode toggle
- ✅ Tailwind CSS utility classes

## Project structure

```
src/
  api/index.js          ← Axios instance with auth interceptors
  stores/auth.js        ← Pinia auth store (persisted to localStorage)
  stores/toast.js       ← Toast notifications
  router/index.js       ← Vue Router + auth guards
  views/
    LoginView.vue
    DashboardView.vue
    CampaignsView.vue
    ContactsView.vue
    TemplatesView.vue
    AnalyticsView.vue
    ComposeView.vue
    AppLayout.vue
  components/
    AppSidebar.vue
    AppTopbar.vue
    CampaignsTable.vue
    ToastContainer.vue
```
