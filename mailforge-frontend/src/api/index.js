import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((cfg) => {
  const raw = localStorage.getItem("mailforge-auth");
  if (raw) {
    try {
      const { accessToken } = JSON.parse(raw);
      if (accessToken) cfg.headers.Authorization = `Bearer ${accessToken}`;
    } catch (_) {}
  }
  return cfg;
});

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const raw = localStorage.getItem("mailforge-auth");
        const { refreshToken } = JSON.parse(raw);
        const { data } = await axios.post("/api/auth/refresh", {
          refresh_token: refreshToken,
        });
        const stored = JSON.parse(localStorage.getItem("mailforge-auth"));
        stored.accessToken = data.access_token;
        stored.refreshToken = data.refresh_token;
        localStorage.setItem("mailforge-auth", JSON.stringify(stored));
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (_) {
        localStorage.removeItem("mailforge-auth");
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  },
);

export default api;
