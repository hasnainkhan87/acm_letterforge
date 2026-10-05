import { useState } from "react";
import { api, LetterDraft, Party, Signatory } from "../api";

const Block = ({ label, p }: { label: string; p: Party }) => (
  <div className="mb-4"><p className="font-semibold">{label}</p><p>{p.name}</p><p>{p.position}</p><p>{p.organization}</p></div>
);
// A4-proportioned page. The letterhead area is a visual stand-in; exported files use the real template.
export default function Preview({ letter, templateName, templateId, sigs }: { letter: LetterDraft; templateName: string; templateId: number; sigs: Signatory[] }) {
  const [bad, setBad] = useState<number | null>(null);  // template ids whose header image failed to load
  return (
    <div style={{ fontSize: `${letter.font_size * 1.18}px`, fontFamily: { "Times New Roman": '"Times New Roman", Times, serif', Arial: "Arial, Helvetica, sans-serif", Calibri: "Calibri, Carlito, sans-serif" }[letter.font_name] }} className="mx-auto aspect-[1/1.414] w-full max-w-[560px] flex flex-col overflow-auto rounded-lg bg-white p-8 leading-relaxed text-slate-900 shadow-xl ring-1 ring-white/10">
      {bad !== templateId
        ? <img src={`/api/templates/${templateId}/letterhead`} onError={() => setBad(templateId)} className="mb-4 w-full" alt="" />
        : <div className="mb-6 border-b-2 border-slate-800 pb-2 text-center text-lg font-bold">{templateName}</div>}
      <Block label="From:" p={letter.sender} />
      {letter.through && <Block label="Through:" p={letter.through} />}
      <Block label="To:" p={letter.recipient} />
      <p className="mb-3">Date: {new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}</p>
      <p className="mb-3 font-bold">Subject: {letter.subject}</p>
      <p className="mb-2">{letter.salutation},</p>
      {letter.body.split("\n\n").map((t, i) => <p key={i} className="mb-2 whitespace-pre-line text-justify">{t}</p>)}
      <p className="mb-6">Thank you.</p>
      <div className="mt-auto grid grid-cols-3 gap-4 pt-6">
        {(sigs.length === 2 ? [sigs[0], null, sigs[1]] : [sigs[0] ?? null, sigs[1] ?? null, sigs[2] ?? null]).map((s, i) => !s ? <div key={i} /> : (
          <div key={s.id}>
            {s.signature_path && <img src={api.fileUrl(s.signature_path)} className="mb-1 h-10 object-contain" alt="" />}
            <p className="font-semibold">{s.name}</p><p>{s.position}</p><p>{s.organization}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
