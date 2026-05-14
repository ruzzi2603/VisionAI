import { useEffect, useState } from "react";
export default function useAlertsSocket(token){const [alerts,setAlerts]=useState([]);useEffect(()=>{if(!token)return; const ws=new WebSocket((import.meta.env.VITE_WS_URL||"ws://localhost:8000/ws/alerts/").trim()); ws.onmessage=(e)=>setAlerts((p)=>[JSON.parse(e.data),...p].slice(0,20)); return ()=>ws.close();},[token]); return alerts;}
