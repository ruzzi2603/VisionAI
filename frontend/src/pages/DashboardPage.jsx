import { useEffect, useMemo, useRef, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import api from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import useAlertsSocket from "../hooks/useAlertsSocket";

const colors = ["#22d3ee", "#f59e0b", "#ef4444", "#8b5cf6"];
const mediaBase = (import.meta.env.VITE_BACKEND_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

function formatDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("pt-BR");
}

export default function DashboardPage() {
  const { token, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [persistedAlerts, setPersistedAlerts] = useState([]);
  const [selectedImage, setSelectedImage] = useState("");
  const [selectedVideo, setSelectedVideo] = useState("");
  const [selectedLiveCameraId, setSelectedLiveCameraId] = useState(null);
  const [selectedLive, setSelectedLive] = useState("");
  const socketAlerts = useAlertsSocket(token);
  const bootstrappedRef = useRef(false);

  useEffect(() => {
    if (!token || bootstrappedRef.current) return;
    bootstrappedRef.current = true;
    api.get("/dashboard/stats/").then((r) => setStats(r.data)).catch(() => {});
    api.get("/cameras/").then(async (r) => {
      const initial = r.data.results || r.data || [];
      setCameras(initial);
      if (initial.length === 0) {
        await api.post("/cameras/discover_local/");
        const refreshed = await api.get("/cameras/");
        setCameras(refreshed.data.results || refreshed.data || []);
      }
    }).catch(() => {});
    api.get("/alerts/?limit=30").then((r) => setPersistedAlerts(r.data.results || r.data || [])).catch(() => {});
  }, [token]);

  const allAlerts = useMemo(() => {
    const merged = [...socketAlerts, ...persistedAlerts];
    const dedup = new Map();
    merged.forEach((a, idx) => {
      const key = a.alert_id || a.id || `${a.event_id || "ws"}-${idx}`;
      if (!dedup.has(key)) dedup.set(key, a);
    });
    return Array.from(dedup.values()).slice(0, 30);
  }, [socketAlerts, persistedAlerts]);

  const deleteIncident = async (eventId) => {
    if (!eventId) return;
    await api.delete(`/events/${eventId}/`);
    setPersistedAlerts((prev) => prev.filter((a) => a.event_id !== eventId));
  };

  const refreshCameraStatus = async (cameraId) => {
    await api.post(`/cameras/${cameraId}/ping/`);
    const updated = await api.get("/cameras/");
    setCameras(updated.data.results || updated.data || []);
  };

  const discoverLocalCameras = async () => {
    await api.post("/cameras/discover_local/");
    const updated = await api.get("/cameras/");
    setCameras(updated.data.results || updated.data || []);
  };

  const openSignedLive = async (cameraId) => {
    const { data } = await api.get(`/cameras/${cameraId}/signed_live_url/`);
    if (!data?.url) return;
    setSelectedLiveCameraId(cameraId);
    setSelectedLive(`${mediaBase}${data.url}`);
  };

  useEffect(() => {
    if (!selectedLiveCameraId) return;
    const refresh = async () => {
      try {
        const { data } = await api.get(`/cameras/${selectedLiveCameraId}/signed_live_url/`);
        if (data?.url) setSelectedLive(`${mediaBase}${data.url}`);
      } catch {
        // keep last working URL until next attempt
      }
    };
    const interval = setInterval(refresh, 45000);
    return () => clearInterval(interval);
  }, [selectedLiveCameraId]);

  return (
    <div className="p-6 md:p-10">
      <header className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">VisionGuard AI Command Center</h1>
          <p className="text-cyan-300">Monitoramento inteligente em tempo real</p>
        </div>
        <button onClick={logout} className="px-4 py-2 rounded bg-slate-800 border border-slate-600">
          Sair
        </button>
      </header>

      <section className="grid md:grid-cols-4 gap-4 mb-8">
        {["total_cameras", "online_cameras", "total_events", "open_alerts"].map((k) => (
          <div key={k} className="rounded-xl p-4 border border-cyan-700/30 bg-cyber-card/70">
            <p className="text-sm text-slate-400">{k}</p>
            <p className="text-2xl font-bold">{stats ? stats[k] : "-"}</p>
          </div>
        ))}
      </section>

      <section className="rounded-xl p-4 border border-cyan-500/30 bg-cyber-card/70 mb-8">
        <h2 className="text-xl mb-3">Cameras Conectadas ({cameras.length}) - Online: {cameras.filter((c) => c.is_online).length}</h2>
        <button
          onClick={discoverLocalCameras}
          className="mb-3 px-3 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-sm font-medium"
        >
          Detectar Cameras Locais
        </button>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
          {cameras.map((camera) => (
            <div key={camera.id} className="p-3 rounded bg-slate-900 border border-slate-700">
              <p className="font-semibold">{camera.name}</p>
              <p className="text-sm text-slate-400">Codigo: {camera.camera_code}</p>
              <p className="text-sm text-slate-400">Status: {camera.is_online ? "online" : "offline"}</p>
              <button
                onClick={() => openSignedLive(camera.id)}
                className="mt-2 px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-sm font-medium"
              >
                Ver ao vivo
              </button>
              <button
                onClick={() => refreshCameraStatus(camera.id)}
                className="mt-2 ml-2 px-3 py-1 rounded bg-slate-700 hover:bg-slate-600 text-sm font-medium"
              >
                Atualizar status
              </button>
            </div>
          ))}
        </div>
      </section>

      <section className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-xl p-4 border border-violet-500/30 bg-cyber-card/70">
          <h2 className="text-xl mb-3">Alertas em Tempo Real</h2>
          <div className="space-y-3 max-h-[32rem] overflow-auto">
            {allAlerts.length === 0 && <p className="text-slate-400">Nenhum alerta recebido ainda.</p>}
            {allAlerts.map((a, idx) => {
              const imageUrl = a.image_url ? `${mediaBase}${a.image_url}` : "";
              const videoUrl = a.video_url ? `${mediaBase}${a.video_url}` : "";
              return (
                <div key={`${a.id || a.alert_id || "ws"}-${idx}`} className="p-3 rounded bg-slate-900 border border-slate-700">
                  <p className="font-semibold">{a.event_type || "alerta"} | {a.risk_level}</p>
                  <p className="text-sm text-slate-400">Camera: {a.camera_id}</p>
                  <p className="text-sm text-slate-400">Status: {a.status || (a.is_active ? "ongoing" : "ended")}</p>
                  <p className="text-sm text-slate-400">Inicio: {formatDateTime(a.started_at || a.timestamp)}</p>
                  <p className="text-sm text-slate-400">Fim: {a.ended_at ? formatDateTime(a.ended_at) : "Ainda acontecendo"}</p>
                  {imageUrl && (
                    <button
                      onClick={() => setSelectedImage(imageUrl)}
                      className="mt-2 px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-sm font-medium"
                    >
                      Ver Momento
                    </button>
                  )}
                  {videoUrl && (
                    <button
                      onClick={() => setSelectedVideo(videoUrl)}
                      className="mt-2 ml-2 px-3 py-1 rounded bg-violet-600 hover:bg-violet-500 text-sm font-medium"
                    >
                      Ver Video
                    </button>
                  )}
                  {a.event_id && (
                    <button
                      onClick={() => deleteIncident(a.event_id)}
                      className="mt-2 ml-2 px-3 py-1 rounded bg-red-700 hover:bg-red-600 text-sm font-medium"
                    >
                      Apagar
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-xl p-4 border border-cyan-500/30 bg-cyber-card/70 h-96">
          <h2 className="text-xl mb-3">Distribuicao de Risco</h2>
          <ResponsiveContainer width="100%" height="85%">
            <PieChart>
              <Pie data={(stats?.risk_distribution || []).map((r) => ({ name: r.risk_level, value: r.total }))} dataKey="value" nameKey="name" outerRadius={110}>
                {(stats?.risk_distribution || []).map((_, i) => (
                  <Cell key={i} fill={colors[i % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </section>

      {selectedImage && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-6" onClick={() => setSelectedImage("")}>
          <img src={selectedImage} alt="Evidencia do alerta" className="max-w-full max-h-full rounded-lg border border-cyan-500/40" />
        </div>
      )}

      {selectedVideo && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-6" onClick={() => setSelectedVideo("")}>
          <video src={selectedVideo} controls autoPlay className="max-w-full max-h-full rounded-lg border border-violet-500/40" />
        </div>
      )}

      {selectedLive && (
        <div className="fixed inset-0 z-50 bg-black/80 flex flex-col items-center justify-center p-6" onClick={() => { setSelectedLive(""); setSelectedLiveCameraId(null); }}>
          <div className="max-w-4xl w-full">
            <img 
              src={selectedLive}
              alt="Camera ao vivo - Stream MJPEG" 
              className="w-full rounded-lg border border-cyan-500/40"
              onError={(e) => console.error("Stream error:", e)}
            />
            <p className="text-center text-slate-300 mt-2 text-sm">Clique para fechar | Stream em tempo real</p>
          </div>
        </div>
      )}
    </div>
  );
}
