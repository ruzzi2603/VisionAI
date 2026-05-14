import { createContext, useContext, useMemo, useState } from "react";
const AuthContext=createContext(null);
export function AuthProvider({children}){const [token,setToken]=useState(localStorage.getItem("vg_token")||"");const value=useMemo(()=>({token,login:(t)=>{localStorage.setItem("vg_token",t);setToken(t);},logout:()=>{localStorage.removeItem("vg_token");setToken("");}}),[token]);return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>}
export function useAuth(){return useContext(AuthContext)}
