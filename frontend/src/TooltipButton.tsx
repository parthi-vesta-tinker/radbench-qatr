import { useEffect, useId, useState, type ButtonHTMLAttributes } from 'react';

/** Hoverable and keyboard-accessible; Escape dismisses without moving focus. */
export function TooltipButton({ label, side = 'left', children, ...props }:
  ButtonHTMLAttributes<HTMLButtonElement> & { label: string; side?: 'left' | 'right' | 'bottom' }) {
  const id = useId();
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const open = (hovered || focused) && !dismissed;
  useEffect(() => {
    if (!open) return;
    const dismiss = (event: KeyboardEvent) => { if (event.key === 'Escape') setDismissed(true); };
    document.addEventListener('keydown', dismiss);
    return () => document.removeEventListener('keydown', dismiss);
  }, [open]);
  return <span className={`tooltip-control tooltip-${side}`}
    onMouseEnter={() => { setHovered(true); setDismissed(false); }} onMouseLeave={() => setHovered(false)}
    onFocus={() => { setFocused(true); setDismissed(false); }} onBlur={() => setFocused(false)}>
    <button {...props} type={props.type ?? 'button'} aria-label={label} aria-describedby={open ? id : undefined}
      onClick={event => { if (props["aria-disabled"] === true || props["aria-disabled"] === "true") { event.preventDefault(); return; } setDismissed(true); props.onClick?.(event); }}>{children}</button>
    {open && <span id={id} role="tooltip" className="control-tooltip">{label}</span>}
  </span>;
}
