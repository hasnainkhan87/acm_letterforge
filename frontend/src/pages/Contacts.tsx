import { useEffect, useState } from "react";
import { api, Contact } from "../api";
import { Button, Card, Input } from "../ui";

const empty = { name: "", position: "", organization: "" };
export default function Contacts() {
  const [list, setList] = useState<Contact[]>([]);
  const [form, setForm] = useState(empty);
  const load = () => api.contacts().then(setList);
  useEffect(() => { load(); }, []);
  async function add(e: React.FormEvent) { e.preventDefault(); await api.saveContact(form); setForm(empty); load(); }
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card>
        <h2 className="mb-1 font-semibold">Add saved details</h2>
        <p className="mb-4 text-sm text-muted">These appear in the From / Through / To dropdowns.</p>
        <form onSubmit={add} className="space-y-3">
          {(["name", "position", "organization"] as const).map(k => (
            <Input key={k} required placeholder={k[0].toUpperCase() + k.slice(1)} value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} />
          ))}
          <Button type="submit">Save</Button>
        </form>
      </Card>
      <div className="space-y-3">
        {list.map(c => (
          <Card key={c.id} className="flex items-center justify-between gap-3">
            <div><p className="font-medium">{c.name}</p><p className="text-sm text-muted">{c.position}, {c.organization}</p></div>
            <Button variant="destructive" onClick={async () => { await api.deleteContact(c.id); load(); }}>Delete</Button>
          </Card>
        ))}
      </div>
    </div>
  );
}
