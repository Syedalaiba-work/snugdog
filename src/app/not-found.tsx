import type { Metadata } from "next";
import { Terrier } from "@/components/doodles";
import { Button } from "@/components/ui/Button";
import s from "./not-found.module.css";

export const metadata: Metadata = {
  title: "Page not found — SNUGDOG",
  robots: { index: false },
};

export default function NotFound() {
  return (
    <main id="main" className={s.page}>
      <Terrier className={s.dog} />
      <p className="label">Error 404</p>
      <h1 className={`display ${s.title}`}>Snug can&rsquo;t find this one.</h1>
      <p className={s.lede}>The page you were looking for has been eaten, moved, or never existed.</p>
      <Button href="/">Back to the hot dogs</Button>
    </main>
  );
}
