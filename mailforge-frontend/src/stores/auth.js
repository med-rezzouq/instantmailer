import { defineStore } from "pinia";
import { ref, computed } from "vue";
import api from "@/api";

export const useAuthStore = defineStore(
  "auth",
  () => {
    const accessToken = ref(null);
    const refreshToken = ref(null);
    const user = ref(null);

    const isAuthenticated = computed(() => !!accessToken.value);

    async function login(email, password) {
      const { data } = await api.post("/auth/login", { email, password });
      accessToken.value = data.access_token;
      refreshToken.value = data.refresh_token;
      await fetchUser();
    }

    async function register(name, email, password) {
      const { data } = await api.post("/auth/register", {
        name,
        email,
        password,
      });
      accessToken.value = data.access_token;
      refreshToken.value = data.refresh_token;
      await fetchUser();
    }

    async function fetchUser() {
      const { data } = await api.get("/auth/me");
      user.value = data;
    }

    function logout() {
      accessToken.value = null;
      refreshToken.value = null;
      user.value = null;
    }

    return {
      accessToken,
      refreshToken,
      user,
      isAuthenticated,
      login,
      register,
      fetchUser,
      logout,
    };
  },
  {
    persist: {
      key: "mailforge-auth",
      paths: ["accessToken", "refreshToken", "user"],
    },
  },
);
