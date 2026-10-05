import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, Letter, Style } from "../api";
import { Button, Select, Textarea } from "../ui";

export default function Dashboard() {
  const nav = useNavigate();
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState<Style>("concise");
  const [recent, setRecent] = useState<Letter[]>([]);
  useEffect(() => { api.letters().then(l => setRecent(l.slice(0, 5))).catch(() => {}); }, []);
  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-line bg-surface p-6 sm:p-8">
        <h2 className="text-2xl text-white sm:text-3xl">What does this letter need to say?</h2>
        <p className="mt-1 max-w-xl text-muted">Describe it in a line or two. The subject and body are drafted for you, and the letterhead and signatures are filled in automatically.</p>
        <Textarea rows={3} className="mt-5" value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Need permission from the Mechanical Department to store decoration materials from 29 September to 1 October for ACM Hack Days." />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Select className="w-44" value={style} onChange={e => setStyle(e.target.value as Style)}>
            <option value="very_short">Very short</option><option value="concise">Concise</option><option value="formal">Formal</option><option value="detailed">Detailed</option>
          </Select>
          <Button disabled={!prompt.trim()} onClick={() => nav("/generate", { state: { prompt, style } })}>Draft the letter</Button>
          <Link to="/generate" className="text-sm text-muted underline-offset-4 hover:underline">or start from a blank letter</Link>
        </div>
      </section>
      <section>
        <div className="mb-3 flex items-baseline justify-between"><h2 className="text-xl text-white">Recent letters</h2><Link to="/letters" className="text-sm text-muted underline-offset-4 hover:underline">See all</Link></div>
        {recent.length ? (
          <ul className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
            {recent.map(l => (
              <li key={l.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
                <div className="min-w-0"><p className="truncate font-medium">{l.subject}</p><p className="text-sm text-muted">To {l.recipient.name} · {new Date(l.created_at).toLocaleDateString()}</p></div>
                <div className="flex gap-2"><a href={api.exportUrl(l.id, "pdf")}><Button variant="outline" className="h-9">PDF</Button></a><a href={api.exportUrl(l.id, "docx")}><Button variant="outline" className="h-9">DOCX</Button></a></div>
              </li>
            ))}
          </ul>
        ) : <p className="rounded-2xl border border-dashed border-line bg-surface/60 px-4 py-6 text-center text-muted">Your exported letters will show up here.</p>}
      </section>
    </div>
  );
}
