import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { getActivePinia } from "pinia";

const routes = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: () => import("@/views/AppLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      { path: "", redirect: "/dashboard" },
      {
        path: "dashboard",
        name: "dashboard",
        component: () => import("@/views/DashboardView.vue"),
      },
      {
        path: "campaigns",
        name: "campaigns",
        component: () => import("@/views/CampaignsView.vue"),
      },
      {
        path: "compose",
        name: "compose",
        component: () => import("@/views/ComposeView.vue"),
      },
      {
        path: "campaigns/:id/edit",
        name: "campaign-edit",
        component: () => import("@/views/ComposeView.vue"),
        props: true,
      },

      // Single route for both groups and contacts
      {
        path: "contacts/:groupId?",
        name: "contacts",
        component: () => import("@/views/ContactsView.vue"),
        props: true,
      },

      {
        path: "templates",
        name: "templates",
        component: () => import("@/views/TemplatesView.vue"),
      },
      {
        path: "analytics",
        name: "analytics",
        component: () => import("@/views/AnalyticsView.vue"),
      },
      {
        path: "smtp",
        name: "smtp",
        component: () => import("@/views/SmtpView.vue"),
      },
      // NEW: tracking domains
      {
        path: "tracking",
        name: "tracking",
        component: () => import("@/views/TrackingView.vue"),
      },
      {
        path: "campaignTracking/:campaign_id?",
        name: "campaignTracking",
        component: () => import("@/views/CampaignTrackingView.vue"),
        props: true,
      },
      // in router/index.js children
      {
        path: "mailboxes",
        name: "mailboxes",
        component: () => import("@/views/MailboxesView.vue"),
      },
      // in router/index.js children
      {
        path: "imapmailboxes",
        name: "imapmailboxes",
        component: () => import("@/views/ImapMailBoxesView.vue"),
      },
      {
        path: "warmup",
        name: "warmup",
        component: () => import("@/views/WarmupView.vue"),
      },
    ],
  },
  { path: "/:pathMatch(.*)*", redirect: "/dashboard" },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  if (!getActivePinia()) return;
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.isAuthenticated) return { name: "login" };
  if (to.meta.public && auth.isAuthenticated) return { path: "/dashboard" };
});

export default router;
