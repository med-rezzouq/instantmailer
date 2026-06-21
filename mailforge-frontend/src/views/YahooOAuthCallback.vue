<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "@/api";

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const errorMessage = ref("");

onMounted(async () => {
  const code = route.query.code;
  const state = route.query.state;
  const error = route.query.error;
  const errorDescription = route.query.error_description;

  console.log("Yahoo callback component mounted");
  console.log("full url:", window.location.href);
  console.log("query:", route.query);

  if (error) {
    errorMessage.value =
      errorDescription || error || "Yahoo authentication failed";
    loading.value = false;
    return;
  }

  if (!code || !state) {
    errorMessage.value = "Missing OAuth callback parameters";
    loading.value = false;
    return;
  }

  try {
    console.log("POSTing Yahoo callback...");

    const res = await api.post("/mailboxes/oauth/yahoo/callback", {
      code,
      state,
    });

    console.log("Yahoo callback success:", res.data);

    await router.replace({
      path: "/mailboxes",
      query: { mailbox_connected: "yahoo" },
    });
  } catch (err) {
    console.error("Yahoo callback POST failed:", err);
    console.error("response:", err?.response);
    console.error("data:", err?.response?.data);

    errorMessage.value =
      err?.response?.data?.detail ||
      err?.message ||
      "Failed to complete Yahoo mailbox connection";

    loading.value = false;
  }
});
</script>
