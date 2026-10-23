import { RiseLines } from "@/components/motion/ScrollReveals";
import s from "./Locations.module.css";

// PLACEHOLDER DATA: neighbourhoods, addresses and hours are invented for layout.
// Replace with the real shops before launch.
const SHOPS = [
  { area: "Old Market", address: "12 Market Lane", hours: "Mon to Sun, 11 to late", status: "Open now" },
  { area: "Riverside", address: "48 Quay Street", hours: "Tue to Sun, 12 to 10", status: "Open now" },
  { area: "Northgate", address: "3 Foundry Yard", hours: "Opening this winter", status: "Coming soon" },
];

export function Locations() {
  return (
    <section id="locations" className={s.locations} aria-labelledby="locations-title">
      <header className={s.head}>
        <p className={`label ${s.kicker}`} data-rise>
          05 / Locations
        </p>
        <RiseLines id="locations-title" className={`display ${s.title}`} lines={["Come and", "find us."]} />
      </header>

      <ul className={s.list}>
        {SHOPS.map((shop, i) => (
          <li key={shop.area} data-rise>
            <a href="#locations" className={s.row}>
              <span className="label">0{i + 1}</span>
              <span className={`display ${s.area}`}>{shop.area}</span>
              <span className={s.detail}>
                {shop.address}
                <br />
                {shop.hours}
              </span>
              <span className={`label ${s.status}`}>{shop.status}</span>
              <svg className={s.arrow} viewBox="0 0 32 32" width="32" height="32" aria-hidden="true" focusable="false">
                <path d="M6 16h19M17 8l8 8-8 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}
