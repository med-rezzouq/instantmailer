import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000" });

// Attach token on every request
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

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const raw = localStorage.getItem("mailforge-auth");
        const { refreshToken } = JSON.parse(raw);
        const { data } = await axios.post(
          "http://localhost:8000/auth/refresh",
          { refresh_token: refreshToken },
        );
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
