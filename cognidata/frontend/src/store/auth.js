import { create } from "zustand";

const useAuth = create((set) => ({
  token: localStorage.getItem("token") || null,
  setToken: (token) => { localStorage.setItem("token", token); set({ token }); },
  clearToken: () => { localStorage.removeItem("token"); set({ token: null }); },
  getPayload: () => {
    const t = localStorage.getItem("token");
    if (!t) return {};
    try { return JSON.parse(atob(t.split(".")[1])); } catch { return {}; }
  },
}));

export default useAuth;
