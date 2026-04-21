import { useEffect, useRef } from "react";
import { Link, useLocation } from "react-router-dom";

const FEATURES = [
  {
    name: "explore",
    sub: "classic mode. find tracks similar to the ones you love.",
    path: "/explore",
    startHere: true,
  },
  {
    name: "soundtrack your life",
    sub: "describe a moment. hear songs that fit the scene.",
    path: "/soundtrack",
  },
  {
    name: "blind taste test",
    sub: "no names. no clues. just music. how well do you know yourself?",
    path: "/blind-taste-test",
  },
  {
    name: "the time machine",
    sub: "explore the intersection of history and your favorite songs.",
    path: "/time-machine",
  },
  {
    name: "algorithmic capture",
    sub: "how homogenized has your taste become? find your escape routes.",
    path: "/algorithmic-capture",
  },
  {
    name: "the séance",
    sub: "pick a deceased artist and summon their living successors.",
    path: "/seance",
  },
];

export function Landing() {
  const { hash } = useLocation();
  const rootRef = useRef(null);
  const panel2Ref = useRef(null);

  // When arriving with #features, jump straight to panel 2 without animation
  useEffect(() => {
    if (hash === "#features" && rootRef.current && panel2Ref.current) {
      rootRef.current.scrollTo({ top: panel2Ref.current.offsetTop, behavior: "instant" });
    }
  }, [hash]);
  return (
    <div className="landing-root" ref={rootRef}>
      <div className="panels-wrapper">

        {/* ── Panel 1: Splash ─────────────────────────────────────────────── */}
        <section className="panel panel-1">
          <div className="panel-header">
            <span className="panel-wordmark">dscvr</span>
            <span className="panel-pronunciation">/dɪˈskʌv.ə/ • tool</span>
            <hr className="panel-rule" />
          </div>

          <div className="panel-body">
            <p className="splash-paragraph">
              To discover is not merely to look, but to truly perceive. It is
              the convergence of prepared curiosity and divine accident, where a
              mundane observation transforms into a universal law.
            </p>
            <p className="splash-paragraph">
              dscvr is a collection of tools designed to help you understand
              your relationship with music. not what to listen to next, but why
              you listen at all.
            </p>
          </div>

          {/* Scroll indicator — decorative only */}
          <div className="scroll-indicator" aria-hidden="true">
            <svg
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M7 1L7 13M7 13L2 8M7 13L12 8"
                stroke="#000"
                strokeWidth="1"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

        </section>

        {/* ── Panel 2: Feature list ────────────────────────────────────────── */}
        <section className="panel panel-2" id="features" ref={panel2Ref}>
          <div className="panel-header">
            <span className="panel-wordmark">dscvr</span>
            <span className="panel-sub">six ways to dscvr.</span>
            <hr className="panel-rule" />
          </div>

          <div className="panel-body">
            <ul className="feature-list">
              {FEATURES.map((f) => (
                <li key={f.path}>
                  <Link to={f.path} className={`feature-row${f.startHere ? " feature-row--start" : ""}`}>
                    <div className="feature-row-inner">
                      <div className="feature-row-name-line">
                        <span className="feature-row-name">{f.name}</span>
                        {f.startHere && (
                          <span className="feature-start-badge" aria-label="start here">
                            <span className="feature-start-dot" />
                            start here
                          </span>
                        )}
                      </div>
                      <span className="feature-row-sub">{f.sub}</span>
                    </div>
                    <span className="feature-row-arrow" aria-hidden="true">→</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <footer className="panel-footer">
            <p className="panel-footer-text">
              built by <a href="https://pyne.dev" target="_blank" rel="noopener noreferrer" className="footer-link">victor</a>, for those who hear more than music.
            </p>
          </footer>
        </section>

      </div>
    </div>
  );
}
