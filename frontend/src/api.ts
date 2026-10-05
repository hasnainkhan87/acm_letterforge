export interface Party { name: string; position: string; organization: string }
export type FontName = "Calibri" | "Times New Roman" | "Arial";
export type Salutation = "Respected Sir" | "Respected Madam";
export interface Contact extends Party { id: number }
export interface Template { id: number; name: string }
export interface Signatory extends Party { id: number; signature_path: string | null; sort_order: number }
export interface Letter { id: number; template_id: number; sender: Party; recipient: Party; through: Party | null; subject: string; body: string; salutation: Salutation; font_name: FontName; font_size: number; signatory_ids: number[]; created_at: string }
export type LetterDraft = Omit<Letter, "id" | "created_at">;
export type Style = "very_short" | "concise" | "formal" | "detailed";

async function req<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? r.statusText);
  return r.json();
}
const json = (method: string, body: unknown): RequestInit => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const api = {
  contacts: () => req<Contact[]>("/api/contacts"),
  saveContact: (p: Party) => req<Contact>("/api/contacts", json("POST", p)),
  deleteContact: (id: number) => req<unknown>(`/api/contacts/${id}`, { method: "DELETE" }),
  templates: () => req<Template[]>("/api/templates"),
  signatories: () => req<Signatory[]>("/api/signatories"),
  saveSignatory: (id: number | null, f: FormData) => req<Signatory>(id ? `/api/signatories/${id}` : "/api/signatories", { method: id ? "PUT" : "POST", body: f }),
  deleteSignatory: (id: number) => req<unknown>(`/api/signatories/${id}`, { method: "DELETE" }),
  reorder: (ids: number[]) => req<unknown>("/api/signatories/reorder", json("PUT", { ids })),
  generate: (prompt: string, style: Style) => req<{ subject: string; body: string }>("/api/generate", json("POST", { prompt, style })),
  saveLetter: (l: LetterDraft) => req<Letter>("/api/letters", json("POST", l)),
  preview: async (l: LetterDraft) => {
    const r = await fetch("/api/preview", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(l) });
    if (!r.ok) throw new Error("preview failed");
    return { url: URL.createObjectURL(await r.blob()), exact: r.headers.get("X-PDF-Fidelity") === "exact" };
  },
  letters: () => req<Letter[]>("/api/letters"),
  exportUrl: (id: number, fmt: "pdf" | "docx") => `/api/letters/${id}/export?format=${fmt}`,
  fileUrl: (key: string) => `/api/files/${key}`,
};
