import { useEffect, useRef, useState } from 'react';

type Panel = 'reports' | 'studio';
type Size = 'desktop' | 'compact' | 'mobile';
const storageKey = 'vesta.panels.v1';
function screenSize(): Size {
  return window.matchMedia('(max-width: 650px)').matches ? 'mobile'
    : window.matchMedia('(max-width: 1120px)').matches ? 'compact' : 'desktop';
}
function preferences() {
  try {
    const value = JSON.parse(localStorage.getItem(storageKey) ?? '{}');
    return { reports: value?.reports === true, studio: value?.studio === true };
  } catch { return { reports: false, studio: false }; }
}

export function usePanels() {
  const [size, setSize] = useState(screenSize);
  const [collapsed, setCollapsed] = useState(preferences);
  const [compactOpen, setCompactOpen] = useState<Panel | null>(null);
  const [drawer, setDrawer] = useState<Panel | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  useEffect(() => {
    const mobile = window.matchMedia('(max-width: 650px)');
    const compact = window.matchMedia('(max-width: 1120px)');
    const change = () => { setSize(screenSize()); setDrawer(null); setCompactOpen(null); };
    mobile.addEventListener('change', change);
    compact.addEventListener('change', change);
    return () => { mobile.removeEventListener('change', change); compact.removeEventListener('change', change); };
  }, []);
  useEffect(() => {
    try { localStorage.setItem(storageKey, JSON.stringify(collapsed)); } catch { /* In-memory controls still work. */ }
  }, [collapsed]);
  useEffect(() => {
    if (!drawer || size !== 'mobile') return;
    const panel = document.getElementById(`${drawer}-panel`)!;
    const before = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const buttons = () => Array.from(panel.querySelectorAll<HTMLElement>(
      'button:not(:disabled), a[href], input, select, textarea, [tabindex="0"]',
    )).filter(element => element.getClientRects().length > 0);
    buttons()[0]?.focus();
    const key = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); setDrawer(null); }
      if (event.key === 'Tab') {
        const items = buttons();
        const first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', key);
    return () => {
      document.body.style.overflow = before;
      document.removeEventListener('keydown', key);
      const returnTo = opener.current?.getClientRects().length ? opener.current
        : panel.querySelector<HTMLElement>('.panel-heading button');
      returnTo?.focus();
    };
  }, [drawer, size]);
  const isCollapsed = (panel: Panel) => size === 'desktop' ? collapsed[panel] : size === 'compact' && compactOpen !== panel;
  const toggle = (panel: Panel) => {
    if (size === 'mobile') {
      opener.current = document.activeElement as HTMLElement;
      setDrawer(panel);
    } else if (size === 'compact') setCompactOpen(current => current === panel ? null : panel);
    else setCollapsed(current => ({ ...current, [panel]: !current[panel] }));
  };
  return { size, drawer, isCollapsed, toggle, close: () => setDrawer(null) };
}
