import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { api, Contact, FontName, LetterDraft, Party, Salutation, Signatory, Style, Template } from "../api";
import { Button, Card, Input, Label, Select, Textarea } from "../ui";
import Preview from "./Preview";

const blank: Party = { name: "", position: "", organization: "" };

function PartyFields({ title, value, onChange, contacts, onSaved }: { title: string; value: Party; onChange: (p: Party) => void; contacts: Contact[]; onSaved: () => void }) {
  const full = value.name && value.position && value.organization;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">{title}</h3>
        <div className="flex items-center gap-2">
          <Select className="h-8 w-44 py-0 text-xs" value="" onChange={e => { const c = contacts.find(x => x.id === +e.target.value); if (c) onChange({ name: c.name, position: c.position, organization: c.organization }); }}>
            <option value="">Fill from saved…</option>
            {contacts.map(c => <option key={c.id} value={c.id}>{c.name} – {c.position}</option>)}
          </Select>
          <Button variant="ghost" className="h-8 px-2 text-xs" disabled={!full} onClick={async () => { await api.saveContact(value); onSaved(); }}>Save</Button>
        </div>
      </div>
      <div className="grid gap-2 sm:grid-cols-3">
        {(["name", "position", "organization"] as const).map(k => (
          <Input key={k} placeholder={k[0].toUpperCase() + k.slice(1)} value={value[k]} onChange={e => onChange({ ...value, [k]: e.target.value })} />
        ))}
      </div>
    </div>
  );
}

export default function Generate() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [sigs, setSigs] = useState<Signatory[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [salutation, setSalutation] = useState<Salutation>("Respected Sir");
  const loadContacts = () => api.contacts().then(setContacts);
  const [templateId, setTemplateId] = useState(0);
  const [sender, setSender] = useState(blank);
  const [recipient, setRecipient] = useState(blank);
  const [through, setThrough] = useState<Party | null>(null);
  const init = (useLocation().state ?? null) as { prompt?: string; style?: Style } | null;
  const [style, setStyle] = useState<Style>(init?.style ?? "concise");
  const [prompt, setPrompt] = useState(init?.prompt ?? "");
  const [tab, setTab] = useState<"edit" | "preview">("edit");
  // Letter text font/size, remembered between letters on this device
  const [fontName, setFontName] = useState<FontName>(() => { try { return (localStorage.getItem("lf_font") as FontName) || "Calibri"; } catch { return "Calibri"; } });
  const [fontSize, setFontSize] = useState<number>(() => { try { return Number(localStorage.getItem("lf_size")) || 11; } catch { return 11; } });
  useEffect(() => { try { localStorage.setItem("lf_font", fontName); localStorage.setItem("lf_size", String(fontSize)); } catch { /* storage unavailable */ } }, [fontName, fontSize]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [chosen, setChosen] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.templates().then(t => { setTemplates(t); if (t[0]) setTemplateId(t[0].id); });
    api.signatories().then(setSigs);
    loadContacts();
    if (init?.prompt) generate(init.prompt, init.style ?? "concise");  // arrived from Home with a prompt
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const draft: LetterDraft = { template_id: templateId, sender, recipient, through, subject, body, salutation, font_name: fontName, font_size: fontSize, signatory_ids: chosen };
  const chosenSigs = chosen.map(id => sigs.find(s => s.id === id)).filter(Boolean) as Signatory[];

  // Real preview: backend fills the actual .docx and returns a PDF (needs LibreOffice/Word); else falls back to the mock page.
  const [pdf, setPdf] = useState<string | null>(null);
  useEffect(() => {
    if (!templateId) return;
    const h = setTimeout(() => {
      api.preview(draft)
        .then(r => setPdf(old => { if (old) URL.revokeObjectURL(old); return r.exact ? r.url : null; }))
        .catch(() => setPdf(null));
    }, 900);
    return () => clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(draft)]);

  async function generate(pr = prompt, st = style) {
    setBusy(true); setError("");
    try { const r = await api.generate(pr, st); setSubject(r.subject); setBody(r.body); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function exportAs(fmt: "pdf" | "docx") {
    try { const l = await api.saveLetter(draft); window.location.href = api.exportUrl(l.id, fmt); }
    catch (e) { setError((e as Error).message); }
  }
  const toggle = (id: number) => setChosen(c => c.includes(id) ? c.filter(x => x !== id) : c.length >= 3 ? c : [...c, id]);

  const Step = ({ n, title, hint }: { n: number; title: string; hint?: string }) => (
    <div className="mb-4 flex items-center gap-3">
      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-sm text-white">{n}</span>
      <div><h2 className="text-lg leading-tight text-white">{title}</h2>{hint && <p className="text-sm text-muted">{hint}</p>}</div>
    </div>
  );
  const sheet = "space-y-4 border-b border-line p-5 sm:p-6";
  return (
    <div>
      <div className="mb-4 grid grid-cols-2 rounded-xl border border-line bg-surface p-1 text-sm lg:hidden">
        {(["edit", "preview"] as const).map(t => (
          <button key={t} onClick={() => setTab(t)} className={`rounded-lg py-2 font-medium ${tab === t ? "bg-primary text-white" : "text-muted"}`}>{t === "edit" ? "Edit" : "Preview"}</button>
        ))}
      </div>
      <div className="grid items-start gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,540px)]">
        <div className={`overflow-hidden rounded-2xl border border-line bg-surface ${tab === "edit" ? "" : "hidden lg:block"}`}>
          <section className={sheet}>
            <Step n={1} title="Who is it between?" hint="Pick saved details or type them in." />
            <div><Label>Letterhead</Label>
              <Select value={templateId} onChange={e => setTemplateId(+e.target.value)}>{templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</Select></div>
            <PartyFields title="From" value={sender} onChange={setSender} contacts={contacts} onSaved={loadContacts} />
            {through
              ? <><PartyFields title="Through" value={through} onChange={setThrough} contacts={contacts} onSaved={loadContacts} /><Button variant="ghost" className="h-8 px-2 text-xs" onClick={() => setThrough(null)}>Remove Through</Button></>
              : <Button variant="outline" onClick={() => setThrough(blank)}>+ Add Through</Button>}
            <PartyFields title="To" value={recipient} onChange={setRecipient} contacts={contacts} onSaved={loadContacts} />
            <div><Label>Salutation</Label><Select value={salutation} onChange={e => setSalutation(e.target.value as Salutation)}><option>Respected Sir</option><option>Respected Madam</option></Select></div>
          </section>
          <section className={sheet}>
            <Step n={2} title="What should it say?" hint="Describe it, then edit the draft freely." />
            <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
              <div><Label>Style</Label>
                <Select value={style} onChange={e => setStyle(e.target.value as Style)}>
                  <option value="very_short">Very short</option><option value="concise">Concise</option><option value="formal">Formal</option><option value="detailed">Detailed</option>
                </Select></div>
              <Button onClick={() => generate()} disabled={busy || !prompt.trim()}>{busy ? "Drafting…" : "Draft subject & body"}</Button>
            </div>
            <Textarea rows={4} value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Need permission from Mechanical Department to store decoration materials from 29 September to 1 October for ACM Hack Days." />
            {error && <p className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-300">{error}</p>}
            <div><Label>Subject</Label><Input value={subject} onChange={e => setSubject(e.target.value)} /></div>
            <div><Label>Body</Label><Textarea rows={8} value={body} onChange={e => setBody(e.target.value)} /></div>
          </section>
          <section className="space-y-4 p-5 sm:p-6">
            <Step n={3} title="Sign and export" hint="Choose up to 3, in signing order." />
            <div className="flex flex-wrap gap-2">
              {sigs.map(s => (
                <Button key={s.id} variant={chosen.includes(s.id) ? "default" : "outline"} onClick={() => toggle(s.id)}>
                  {chosen.includes(s.id) && `${chosen.indexOf(s.id) + 1}. `}{s.name}
                </Button>
              ))}
              {!sigs.length && <p className="text-sm text-muted">Add signatories first.</p>}
            </div>
            <div className="grid grid-cols-2 gap-3 pt-2">
              <div><Label>Letter font</Label><Select value={fontName} onChange={e => setFontName(e.target.value as FontName)}><option>Calibri</option><option>Times New Roman</option><option>Arial</option></Select></div>
              <div><Label>Font size</Label><Select value={fontSize} onChange={e => setFontSize(+e.target.value)}>{[10, 11, 12, 13, 14].map(n => <option key={n} value={n}>{n} pt</option>)}</Select></div>
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              <Button onClick={() => exportAs("pdf")} disabled={!subject || !body}>Export PDF</Button>
              <Button variant="outline" onClick={() => exportAs("docx")} disabled={!subject || !body}>Export DOCX</Button>
            </div>
          </section>
        </div>
        <div className={`lg:sticky lg:top-6 ${tab === "preview" ? "" : "hidden lg:block"}`}>
          {pdf && <iframe title="Letter preview" src={pdf + "#toolbar=0&navpanes=0"} className="hidden aspect-[1/1.414] w-full rounded-lg bg-white shadow-xl ring-1 ring-white/10 lg:block" />}
          <div className={pdf ? "lg:hidden" : ""}>
            <Preview letter={draft} templateId={templateId} templateName={templates.find(t => t.id === templateId)?.name ?? ""} sigs={chosenSigs} />
          </div>
        </div>
      </div>
    </div>
  );
}
