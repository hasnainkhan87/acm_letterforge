// Small design-system primitives (shadcn-style conventions, LetterForge tokens).
import React from "react";
const cx = (...c: (string | false | undefined)[]) => c.filter(Boolean).join(" ");

export function Button({ variant = "default", className, ...p }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "default" | "outline" | "ghost" | "destructive" }) {
  const v = { default: "bg-primary text-white hover:bg-primary-soft", outline: "border border-line bg-surface text-main hover:bg-line/50",
    ghost: "text-main hover:bg-line/50", destructive: "border border-red-400/40 bg-surface text-red-300 hover:bg-red-500/10" }[variant];
  return <button className={cx("inline-flex h-10 items-center justify-center rounded-lg px-4 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent disabled:cursor-not-allowed disabled:opacity-45", v, className)} {...p} />;
}
// full width unless the caller sets its own width class (w-44, sm:w-auto, ...)
const w = (c?: string) => (c && /(^|\s)(sm:|lg:)?w-/.test(c) ? "" : "w-full");
const field = "rounded-lg border border-line bg-field px-3 py-2 text-[15px] text-main outline-none transition placeholder:text-muted/60 focus:border-primary-soft focus:ring-2 focus:ring-primary/40";
export const Input = (p: React.InputHTMLAttributes<HTMLInputElement>) => <input {...p} className={cx(field, w(p.className), p.className)} />;
export const Textarea = (p: React.TextareaHTMLAttributes<HTMLTextAreaElement>) => <textarea {...p} className={cx(field, w(p.className), "leading-relaxed", p.className)} />;
export const Select = (p: React.SelectHTMLAttributes<HTMLSelectElement>) => <select {...p} className={cx(field, w(p.className), p.className)} />;
export const Label = (p: React.LabelHTMLAttributes<HTMLLabelElement>) => <label {...p} className={cx("mb-1.5 block text-sm font-medium text-muted", p.className)} />;
export const Card = ({ className, ...p }: React.HTMLAttributes<HTMLDivElement>) => <div className={cx("rounded-2xl border border-line bg-surface p-5", className)} {...p} />;
