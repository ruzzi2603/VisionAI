import axios from "axios";
const api=axios.create({baseURL:import.meta.env.VITE_API_URL||"http://localhost:8000/api"});
api.interceptors.request.use((config)=>{const token=localStorage.getItem("vg_token"); if(token){config.headers.Authorization=`Bearer ${token}`;} return config;});
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const url = error?.config?.url || "";
    if (status === 401 && !url.includes("/auth/login/")) {
      localStorage.removeItem("vg_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
export default api;
