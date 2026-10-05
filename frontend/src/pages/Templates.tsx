import { useEffect, useState } from "react";
import { api, Template } from "../api";
import { Card } from "../ui";
export default function Templates() {
  const [t, setT] = useState<Template[]>([]);
  useEffect(() => { api.templates().then(setT); }, []);
  return <div className="grid gap-3 sm:grid-cols-2">{t.map(x => <Card key={x.id}>{x.name}</Card>)}</div>;
}
