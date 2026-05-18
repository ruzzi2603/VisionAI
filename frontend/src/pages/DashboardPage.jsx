import { useEffect, useMemo, useRef, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import api from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import useAlertsSocket from "../hooks/useAlertsSocket";
import MJPEGStream from "../components/MJPEGStream";

const colors = ["#22d3ee", "#f59e0b", "#ef4444", "#8b5cf6"];
const defaultBackend = "http://localhost:8000";
const mediaBase = (
  import.meta.env.VITE_BACKEND_BASE_URL ||
  (import.meta.env.VITE_API_URL || defaultBackend).replace(/\/api\/?$/, "") ||
  defaultBackend
).replace(/\/$/, "");

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
  const [visionRunning, setVisionRunning] = useState(false);
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
    checkVisionStatus();
  }, [token]);

  const checkVisionStatus = async () => {
    try {
      const { data } = await api.get("/cameras/vision_status/");
      setVisionRunning(data.running);
    } catch {
      setVisionRunning(false);
    }
  };

  const startVision = async () => {
    try {
      await api.post("/cameras/vision_start/");
      setVisionRunning(true);
      setTimeout(checkVisionStatus, 2000);
    } catch (error) {
      console.error("Erro ao iniciar câmera:", error);
      alert("Erro ao iniciar câmera");
    }
  };

  const stopVision = async () => {
    try {
      await api.post("/cameras/vision_stop/");
      setVisionRunning(false);
    } catch (error) {
      console.error("Erro ao parar câmera:", error);
      alert("Erro ao parar câmera");
    }
  };

  const allAlerts = useMemo(() => {
    const merged = [...socketAlerts, ...persistedAlerts];
    const dedup = new Map();
    merged.forEach((a, idx) => {
      const key = a.alert_id || a.id || `${a.event_id || "ws"}-${idx}`;
      if (!dedup.has(key)) dedup.set(key, a);
    });
    // Ordenar por risco (CRITICAL > HIGH > MEDIUM > LOW)
    const riskOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
    return Array.from(dedup.values())
      .sort((a, b) => (riskOrder[a.risk_level] || 3) - (riskOrder[b.risk_level] || 3))
      .slice(0, 30);
  }, [socketAlerts, persistedAlerts]);

  const getRiskColor = (riskLevel) => {
    const colors = {
      CRITICAL: "border-red-500 bg-red-900/20",
      HIGH: "border-orange-500 bg-orange-900/20",
      MEDIUM: "border-yellow-500 bg-yellow-900/20",
      LOW: "border-green-500 bg-green-900/20",
    };
    return colors[riskLevel] || "border-slate-500 bg-slate-900/20";
  };

  const getRiskIcon = (riskLevel) => {
    const icons = {
      CRITICAL: "🔴",
      HIGH: "🟠",
      MEDIUM: "🟡",
      LOW: "🟢",
    };
    return icons[riskLevel] || "❓";
  };

  const riskDistribution = useMemo(() => {
    const dist = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    allAlerts.forEach((a) => {
      const level = a.risk_level || "LOW";
      if (dist.hasOwnProperty(level)) dist[level]++;
    });
    return [
      { name: "🔴 CRÍTICO", value: dist.CRITICAL },
      { name: "🟠 ALTO", value: dist.HIGH },
      { name: "🟡 MÉDIO", value: dist.MEDIUM },
      { name: "🟢 BAIXO", value: dist.LOW },
    ].filter((r) => r.value > 0);
  }, [allAlerts]);

  const riskColors = {
    "🔴 CRÍTICO": "#ef4444",
    "🟠 ALTO": "#f59e0b",
    "🟡 MÉDIO": "#eab308",
    "🟢 BAIXO": "#22c55e",
  };

  const deleteAlert = async (eventId) => {
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
      <button
        onClick={logout}
        className="px-4 py-2 rounded bg-slate-800 border border-slate-600"
      >
        Sair
      </button>
    </header>

    {/* Estatísticas */}
    <section className="grid md:grid-cols-4 gap-4 mb-8">
      {["total_cameras", "online_cameras", "total_events", "open_alerts"].map((k) => (
        <div
          key={k}
          className="rounded-xl p-4 border border-cyan-700/30 bg-cyber-card/70"
        >
          <p className="text-sm text-slate-400">{k}</p>
          <p className="text-2xl font-bold">{stats ? stats[k] : "-"}</p>
        </div>
      ))}
    </section>

    {/* Lista de câmeras */}
    <section className="rounded-xl p-4 border border-cyan-500/30 bg-cyber-card/70 mb-8">
      <h2 className="text-xl mb-3">
        Cameras Conectadas ({cameras.length}) - Online:{" "}
        {cameras.filter((c) => c.is_online).length}
      </h2>
      <div className="flex gap-2 mb-3">
        {visionRunning ? (
          <button
            onClick={stopVision}
            className="px-3 py-1 rounded bg-red-700 hover:bg-red-600 text-sm font-medium"
          >
            ⊘ Desligar Câmera
          </button>
        ) : (
          <button
            onClick={startVision}
            className="px-3 py-1 rounded bg-green-700 hover:bg-green-600 text-sm font-medium"
          >
            ▶ Ligar Câmera
          </button>
        )}
        <button
          onClick={discoverLocalCameras}
          className="px-3 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-sm font-medium"
        >
          Detectar Cameras Locais
        </button>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
        {cameras.map((camera) => (
          <div
            key={camera.id}
            className="p-3 rounded bg-slate-900 border border-slate-700"
          >
            <p className="font-semibold">{camera.name}</p>
            <p className="text-sm text-slate-400">
              Codigo: {camera.camera_code}
            </p>
            <p className="text-sm text-slate-400">
              Status: {camera.is_online ? "online" : "offline"}
            </p>
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

    {/* Vídeo ao vivo (fora do loop) */}
    {selectedLive && (
      <div className="fixed inset-0 z-50 bg-black/80 flex flex-col items-center justify-center p-6"
           onClick={() => { setSelectedLive(""); setSelectedLiveCameraId(null); }}>
        <div className="max-w-4xl w-full">
          <MJPEGStream
            src={selectedLive}
            alt="Camera ao vivo - Stream MJPEG"
          />
          <p className="text-center text-slate-300 mt-2 text-sm">
            Clique para fechar | Stream em tempo real
          </p>
        </div>
      </div>
    )}

    {/* Alertas e distribuição de risco */}
    <section className="grid lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 rounded-xl p-4 border border-violet-500/30 bg-cyber-card/70">
        <h2 className="text-xl mb-3">Alertas em Tempo Real</h2>
        <div className="space-y-3 max-h-[32rem] overflow-auto">
          {allAlerts.length === 0 && (
            <p className="text-slate-400">Nenhum alerta recebido ainda.</p>
          )}
          {allAlerts.map((a, idx) => {
            const imageUrl = a.image_url ? `${mediaBase}${a.image_url}` : "";
            const videoUrl = a.video_url ? `${mediaBase}${a.video_url}` : "";
            return (
              <div
                key={`${a.id || a.alert_id || "ws"}-${idx}`}
                className={`p-3 rounded border ${getRiskColor(a.risk_level)}`}
              >
                <p className="font-semibold text-lg">
                  {getRiskIcon(a.risk_level)} {a.event_type || "alerta"} |{" "}
                  <span className="text-red-300">{a.risk_level}</span>
                </p>
                <p className="text-sm text-slate-300">Camera: {a.camera_id}</p>
                <p className="text-sm text-slate-300">
                  Status: {a.status || (a.is_active ? "ongoing" : "ended")}
                </p>
                <p className="text-sm text-slate-300">
                  Inicio: {formatDateTime(a.started_at || a.timestamp)}
                </p>
                <p className="text-sm text-slate-300">
                  Fim:{" "}
                  {a.ended_at
                    ? formatDateTime(a.ended_at)
                    : "Ainda acontecendo"}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {imageUrl && (
                    <button
                      onClick={() => setSelectedImage(imageUrl)}
                      className="px-2 py-1 rounded bg-cyan-700 hover:bg-cyan-600 text-xs font-medium"
                    >
                      📷 Ver Momento
                    </button>
                  )}
                  {videoUrl && (
                    <button
                      onClick={() => setSelectedVideo(videoUrl)}
                      className="px-2 py-1 rounded bg-violet-700 hover:bg-violet-600 text-xs font-medium"
                    >
                      🎬 Ver Video
                    </button>
                  )}
                  {a.event_id && (
                    <button
                      onClick={() => deleteIncident(a.event_id)}
                      className="px-2 py-1 rounded bg-red-800 hover:bg-red-700 text-xs font-medium"
                    >
                      ✕ Apagar
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-xl p-4 border border-cyan-500/30 bg-cyber-card/70 h-96">
        <h2 className="text-xl mb-3">Distribuição de Risco</h2>
        {riskDistribution.length > 0 ? (
          <ResponsiveContainer width="100%" height="85%">
            <PieChart>
              <Pie
                data={riskDistribution}
                dataKey="value"
                nameKey="name"
                outerRadius={110}
              >
                {riskDistribution.map((r) => (
                  <Cell key={r.name} fill={riskColors[r.name]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-400">
            Nenhum alerta no momento
          </div>
        )}
      </div>
    </section>

    {/* Modais de imagem e vídeo */}
    {selectedImage && (
      <div
        className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-6"
        onClick={() => setSelectedImage("")}
      >
        <img
          src={selectedImage}
          alt="Evidencia do alerta"
          className="max-w-full max-h-full rounded-lg border border-cyan-500/40"
        />
      </div>
    )}

    {selectedVideo && (
      <div
        className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-6"
        onClick={() => setSelectedVideo("")}
      >
        <video
          src={selectedVideo}
          controls
          autoPlay
          className="max-w-full max-h-full rounded-lg border border-violet-500/40"
        />
      </div>
    )}
  </div>
)};
