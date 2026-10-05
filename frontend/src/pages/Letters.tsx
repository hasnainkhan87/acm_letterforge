import { useEffect, useState } from "react";
import { api, Letter } from "../api";
import { Button, Card } from "../ui";
export default function Letters() {
  const [ls, setLs] = useState<Letter[]>([]);
  useEffect(() => { api.letters().then(setLs); }, []);
  if (!ls.length) return <p className="text-muted">No saved letters yet.</p>;
  return (
    <div className="space-y-3">
      {ls.map(l => (
        <Card key={l.id} className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="font-medium">{l.subject}</p><p className="text-sm text-muted">To {l.recipient.name} · {new Date(l.created_at).toLocaleDateString()}</p></div>
          <div className="flex gap-2">
            <a href={api.exportUrl(l.id, "pdf")}><Button variant="outline">PDF</Button></a>
            <a href={api.exportUrl(l.id, "docx")}><Button variant="outline">DOCX</Button></a>
          </div>
        </Card>
      ))}
    </div>
  );
}
