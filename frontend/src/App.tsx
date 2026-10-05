import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Generate from "./pages/Generate";
import Signatories from "./pages/Signatories";
import Letters from "./pages/Letters";
import Templates from "./pages/Templates";
import Contacts from "./pages/Contacts";
import { BRAND, CHAPTER } from "./brand";

const ICONS: Record<string, string> = {
  write: "M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z",
  saved: "M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z",
  sign: "M3 17c3-7 5-7 6-3s3 4 5-1 4-2 7 0",
  people: "M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM22 21v-2a4 4 0 00-3-3.9M16 3.1a4 4 0 010 7.8",
  template: "M4 4h16v16H4zM4 9h16M9 9v11",
};
const Icon = ({ n }: { n: string }) => (
  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d={ICONS[n]} /></svg>
);
// [path, label, icon, shown in mobile tab bar]
const NAV: [string, string, string, boolean][] = [
  ["/generate", "Write", "write", true], ["/letters", "Saved", "saved", true], ["/signatories", "Signatories", "sign", true],
  ["/contacts", "Details", "people", true], ["/templates", "Templates", "template", false],
];
const TITLES: Record<string, string> = { "/": "Welcome", "/generate": "Write a letter", "/letters": "Saved letters", "/signatories": "Signatories", "/contacts": "Saved details", "/templates": "Letterheads" };

export default function App() {
  const { pathname } = useLocation();
  const link = (active: boolean) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${active ? "bg-primary font-medium text-white" : "text-white/70 hover:bg-white/10 hover:text-white"}`;
  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 hidden w-60 flex-col bg-sidebar p-5 lg:flex border-r border-line">
        <Link to="/" className="mb-8 block">
          <div className="rounded-xl bg-white p-3">
            <img src="/logo-nitte.png" alt="NITTE, NMAM Institute of Technology" className="w-full" />
            <img src="/logo-acm.png" alt="ACM" className="mx-auto mt-2 h-14 w-auto" />
          </div>
          <span className="mt-4 block font-serif text-2xl text-white">{BRAND}</span>
          <span className="mt-1.5 block text-[10px] font-medium uppercase tracking-[0.3em] text-accent">{CHAPTER}</span>
        </Link>
        <nav className="space-y-1">{NAV.map(([to, label, ic]) => <NavLink key={to} to={to} className={({ isActive }) => link(isActive)}><Icon n={ic} />{label}</NavLink>)}</nav>
      </aside>
      <header className="flex items-center justify-between bg-sidebar px-4 py-3 text-white lg:hidden border-b border-line">
        <Link to="/" className="flex items-center gap-3"><span className="rounded-lg bg-white p-1"><img src="/logo-acm.png" alt="ACM" className="h-8 w-auto" /></span><span className="font-serif text-xl">{BRAND}</span></Link>
        <Link to="/templates" className="text-xs text-white/70">Letterheads</Link>
      </header>
      <main className="px-4 pb-24 pt-6 lg:pl-60 lg:pb-10">
        <div className="mx-auto max-w-6xl lg:px-10">
          <h1 className="mb-6 text-3xl text-white">{TITLES[pathname] ?? BRAND}</h1>
          <Routes>
            <Route path="/" element={<Dashboard />} /><Route path="/generate" element={<Generate />} />
            <Route path="/letters" element={<Letters />} /><Route path="/templates" element={<Templates />} />
            <Route path="/signatories" element={<Signatories />} /><Route path="/contacts" element={<Contacts />} />
          </Routes>
        </div>
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-10 grid grid-cols-4 border-t border-line bg-surface pb-[env(safe-area-inset-bottom)] lg:hidden">
        {NAV.filter(n => n[3]).map(([to, label, ic]) => (
          <NavLink key={to} to={to} className={({ isActive }) => `flex flex-col items-center gap-0.5 py-2 text-[11px] ${isActive ? "font-semibold text-accent" : "text-muted"}`}><Icon n={ic} />{label}</NavLink>
        ))}
      </nav>
    </div>
  );
}
