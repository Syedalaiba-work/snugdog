import Link from "next/link";
import type { ComponentProps } from "react";
import s from "./Button.module.css";

type Props = ComponentProps<typeof Link> & {
  /** solid: black pill, the one primary action. text: quiet secondary link. */
  variant?: "solid" | "text";
  size?: "md" | "sm";
  /** arrow travels on hover; play sits in a ring for "watch" actions */
  icon?: "arrow" | "play" | "none";
};

const Arrow = () => (
  <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">
    <path d="M2 8h11M8.5 3.5 13 8l-4.5 4.5" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

export function Button({ variant = "solid", size = "md", icon = "arrow", className, children, ...rest }: Props) {
  const classes = [s.btn, s[variant], s[size], className].filter(Boolean).join(" ");
  return (
    <Link className={classes} {...rest}>
      {icon === "play" && (
        <span className={s.play} aria-hidden="true">
          <svg viewBox="0 0 12 12" width="10" height="10" focusable="false">
            <path d="M3 1.5v9l7.5-4.5z" fill="currentColor" />
          </svg>
        </span>
      )}
      <span className={s.text}>{children}</span>
      {icon === "arrow" && (
        // two arrows: one leaves to the right as its twin arrives from the left
        <span className={s.arrow} aria-hidden="true">
          <Arrow />
          <Arrow />
        </span>
      )}
    </Link>
  );
}
