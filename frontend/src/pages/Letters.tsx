import { useEffect, useState } from "react";
import { api, Letter } from "../api";
import { Button, Card } from "../ui";
export default function Letters() {
  const [ls, setLs] = useState<Letter[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { api.letters().then(setLs); }, []);

  async function remove(l: Letter) {
    if (!window.confirm(`Delete "${l.subject}"? This cannot be undone.`)) return;
    try { await api.deleteLetter(l.id); setLs(prev => prev.filter(x => x.id !== l.id)); setError(""); }
    catch { setError("Could not delete the letter. Please try again."); }
  }
  async function removeAll() {
    if (!window.confirm(`Delete all ${ls.length} saved letters? This cannot be undone.`)) return;
    try { await api.deleteAllLetters(); setLs([]); setError(""); }
    catch { setError("Could not delete the letters. Please try again."); }
  }

  if (!ls.length) return <p className="text-muted">No saved letters yet.</p>;
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted">{ls.length} saved {ls.length === 1 ? "letter" : "letters"}</p>
        <Button variant="destructive" onClick={removeAll}>Delete all</Button>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      {ls.map(l => (
        <Card key={l.id} className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="font-medium">{l.subject}</p><p className="text-sm text-muted">To {l.recipient.name} · {new Date(l.created_at).toLocaleDateString()}</p></div>
          <div className="flex gap-2">
            <a href={api.exportUrl(l.id, "pdf")}><Button variant="outline">PDF</Button></a>
            <a href={api.exportUrl(l.id, "docx")}><Button variant="outline">DOCX</Button></a>
            <Button variant="destructive" onClick={() => remove(l)}>Delete</Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
