"use client";
import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/lib/auth";
import { api, VoiceProfile, Project } from "@/lib/api";
import { LogOut, Upload, Mic, Music, Trash2, Download, Loader2 } from "lucide-react";

export function Dashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("projects");
  const [voices, setVoices] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploadName, setUploadName] = useState("");
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [np, setNp] = useState({ vid: "", title: "", lyrics: "" });
  const [creating, setCreating] = useState(false);

  const ld = async () => {
    try {
      const [v, p] = await Promise.all([api.listVoices(), api.listProjects()]);
      setVoices(v.profiles); setProjects(p.projects);
    } catch(e) {}
    setLoading(false);
  };
  useEffect(() => { ld(); }, []);
  useEffect(() => { const i = setInterval(ld, 5000); return () => clearInterval(i); }, []);

  const hu = async (e) => {
    e.preventDefault();
    if (uploadFile == null || uploadName === "") return;
    setUploading(true);
    try { await api.uploadVoice(uploadName, uploadFile); setUploadName(""); setUploadFile(null); ld(); }
    catch(er) { alert(er.message); }
    setUploading(false);
  };

  const hc = async (e) => {
    e.preventDefault();
    if (np.vid === "" || np.title === "" || np.lyrics === "") return;
    setCreating(true);
    try { await api.createProject({voice_profile_id:np.vid,title:np.title,lyrics:np.lyrics}); setNp({vid:"",title:"",lyrics:""}); ld(); }
    catch(er) { alert(er.message); }
    setCreating(false);
  };

  const dv = async (id) => { if (confirm("Delete voice?")) { await api.deleteVoice(id); ld(); } };
  const dp = async (id) => { if (confirm("Delete project?")) { await api.deleteProject(id); ld(); } };
  const rv = voices.filter(v => v.status === "completed");
  const sc = (s) => s==="completed"?"text-green-400":s==="processing"?"text-yellow-400":s==="failed"?"text-red-400":"text-zinc-500";

  if (loading) return <div className="min-h-screen flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-brand-400" /></div>;

  return (
    <div className="min-h-screen bg-zinc-950">
      <header className="glass border-b border-zinc-800">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Music className="w-6 h-6 text-brand-400" />
            <span className="font-semibold text-lg">Singer</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-zinc-400">{user.display_name}</span>
            <button onClick={logout} className="p-2 hover:bg-zinc-800 rounded-lg"><LogOut className="w-4 h-4" /></button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex gap-2 mb-6">
          <button onClick={() => setTab("projects")} className={`px-4 py-2 rounded-lg text-sm font-medium ${tab==="projects"?"bg-brand-600 text-white":"bg-zinc-800 text-zinc-400"}`}>My Songs</button>
          <button onClick={() => setTab("voices")} className={`px-4 py-2 rounded-lg text-sm font-medium ${tab==="voices"?"bg-brand-600 text-white":"bg-zinc-800 text-zinc-400"}`}>My Voices</button>
          <button onClick={() => setTab("create")} className={`px-4 py-2 rounded-lg text-sm font-medium ${tab==="create"?"bg-brand-600 text-white":"bg-zinc-800 text-zinc-400"}`}>Create New</button>
        </div>

        {tab === "projects" && (
          <div className="space-y-3">
            {projects.length === 0 && <p className="text-zinc-500 text-center py-12">No songs yet. Create your first song</p>}
            {projects.map(p => (
              <div key={p.id} className="glass rounded-xl p-4 flex items-center justify-between">
                <div>
                  <h3 className="font-medium">{p.title}</h3>
                  <p className="text-sm text-zinc-400 mt-1">{p.lyrics.slice(0,80)}{p.lyrics.length>80?"...":""}</p>
                  <span className={`text-xs mt-1 inline-block ${sc(p.status)}`}>{p.status}</span>
                </div>
                <div className="flex items-center gap-2">
                  {p.status === "completed" && (
                    <a href={api.getDownloadUrl(p.id)} className="p-2 hover:bg-zinc-700 rounded-lg text-green-400"><Download className="w-4 h-4" /></a>
                  )}
                  <button onClick={() => dp(p.id)} className="p-2 hover:bg-zinc-700 rounded-lg text-red-400"><Trash2 className="w-4 h-4" /></button>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "voices" && (
          <div>
            <form onSubmit={hu} className="glass rounded-xl p-4 mb-6 space-y-3">
              <h3 className="font-medium">Upload Voice Sample</h3>
              <input value={uploadName} onChange={e => setUploadName(e.target.value)} placeholder="Voice name" className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white" required />
              <input type="file" accept="audio/*" onChange={e => setUploadFile(e.target.files[0])} className="w-full text-sm text-zinc-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-brand-600 file:text-white" required />
              <button type="submit" disabled={uploading} className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium">
                {uploading ? "Uploading..." : "Upload Voice"}
              </button>
            </form>

            <div className="space-y-2">
              {voices.length === 0 && <p className="text-zinc-500 text-center py-8">No voice profiles yet</p>}
              {voices.map(v => (
                <div key={v.id} className="glass rounded-lg p-3 flex items-center justify-between">
                  <div>
                    <span className="font-medium text-sm">{v.name}</span>
                    <span className={`text-xs ml-2 ${sc(v.status)}`}>{v.status}</span>
                  </div>
                  <button onClick={() => dv(v.id)} className="p-1.5 hover:bg-zinc-700 rounded text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "create" && (
          <form onSubmit={hc} className="glass rounded-xl p-6 space-y-4 max-w-lg">
            <h3 className="font-medium text-lg">Create New Song</h3>
            {rv.length === 0 && <p className="text-yellow-400 text-sm">Upload a voice sample first in the Voices tab</p>}
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Voice</label>
              <select value={np.vid} onChange={e => setNp({...np, vid: e.target.value})} className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white" required>
                <option value="">Select a voice</option>
                {rv.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Song Title</label>
              <input value={np.title} onChange={e => setNp({...np, title: e.target.value})} placeholder="My Song" className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">Lyrics</label>
              <textarea value={np.lyrics} onChange={e => setNp({...np, lyrics: e.target.value})} rows={4} placeholder="Write lyrics..." className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white resize-none" required />
            </div>
            <button type="submit" disabled={creating || rv.length === 0} className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-medium rounded-lg">
              {creating ? "Creating..." : "Generate Song"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
