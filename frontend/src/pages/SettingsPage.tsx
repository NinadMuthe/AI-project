import { useEffect, useState } from "react";
import api from "../services/api";

export default function SettingsPage(){
  const [profile, setProfile] = useState<{full_name:string;email:string}|null>(null);
  const [error, setError] = useState("");
  useEffect(()=>{api.get("/auth/me").then(response=>setProfile(response.data)).catch(()=>setError("Could not load your account details."));},[]);
  return <div><h1 className="text-2xl font-semibold">Settings</h1><section className="mt-6 max-w-lg border bg-white p-5 shadow-sm"><h2 className="font-medium">Account</h2>{error&&<p className="mt-3 text-red-600">{error}</p>}{!profile&&!error&&<p className="mt-3 text-slate-500">Loading account details…</p>}{profile&&<dl className="mt-4 space-y-3 text-sm"><div><dt className="text-slate-500">Name</dt><dd>{profile.full_name}</dd></div><div><dt className="text-slate-500">Email</dt><dd>{profile.email}</dd></div></dl>}</section></div>}
