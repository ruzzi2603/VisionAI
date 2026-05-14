import { Routes, Route, Navigate } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
function ProtectedRoute({children}){const {token}=useAuth(); return token?children:<Navigate to="/login" replace/>}
export default function App(){return <AuthProvider><Routes><Route path="/login" element={<LoginPage/>}/><Route path="/" element={<ProtectedRoute><DashboardPage/></ProtectedRoute>}/></Routes></AuthProvider>}
