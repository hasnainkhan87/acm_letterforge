import { useEffect, useState } from "react";
import { api, Signatory } from "../api";
import { Button, Card, Input, Label } from "../ui";

const empty = { name: "", position: "", organization: "" };
export default function Signatories() {
  const [list, setList] = useState<Signatory[]>([]);
  const [form, setForm] = useState(empty);
  const [file, setFile] = useState<File | null>(null);
  const [editing, setEditing] = useState<number | null>(null);
  const load = () => api.signatories().then(setList);
  useEffect(() => { load(); }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const f = new FormData();
    Object.entries(form).forEach(([k, v]) => f.append(k, v));
    if (file) f.append("image", file);
    await api.saveSignatory(editing, f);
    setForm(empty); setFile(null); setEditing(null); load();
  }
  async function move(i: number, d: number) {
    const ids = list.map(s => s.id); const j = i + d;
    if (j < 0 || j >= ids.length) return;
    [ids[i], ids[j]] = [ids[j], ids[i]];
    await api.reorder(ids); load();
  }
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <h2 className="mb-4 font-semibold">{editing ? "Edit signatory" : "Add signatory"}</h2>
        <form onSubmit={submit} className="space-y-3">
          {(["name", "position", "organization"] as const).map(k => (
            <div key={k}><Label className="capitalize">{k}</Label><Input required value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} /></div>
          ))}
          <div><Label>Signature image (PNG)</Label><Input type="file" accept="image/png" onChange={e => setFile(e.target.files?.[0] ?? null)} /></div>
          <div className="flex gap-2"><Button type="submit">{editing ? "Save" : "Add"}</Button>
            {editing && <Button type="button" variant="ghost" onClick={() => { setEditing(null); setForm(empty); }}>Cancel</Button>}</div>
        </form>
      </Card>
      <div className="space-y-3">
        {list.map((s, i) => (
          <Card key={s.id} className="flex items-center gap-3">
            {s.signature_path && <img src={api.fileUrl(s.signature_path)} className="h-10 w-20 object-contain" alt="" />}
            <div className="flex-1"><p className="font-medium">{s.name}</p><p className="text-sm text-muted">{s.position}, {s.organization}</p></div>
            <Button variant="ghost" onClick={() => move(i, -1)}>↑</Button><Button variant="ghost" onClick={() => move(i, 1)}>↓</Button>
            <Button variant="outline" onClick={() => { setEditing(s.id); setForm({ name: s.name, position: s.position, organization: s.organization }); }}>Edit</Button>
            <Button variant="destructive" onClick={async () => { await api.deleteSignatory(s.id); load(); }}>Delete</Button>
          </Card>
        ))}
        {!list.length && <p className="text-muted">No signatories yet.</p>}
      </div>
    </div>
  );
}
