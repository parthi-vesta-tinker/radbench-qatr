import { useId, useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

export function StudioDisclosure({ title, preview, children, expandable = true, moreLabel }: {
  title: string; preview: ReactNode; children?: ReactNode; expandable?: boolean; moreLabel?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const id = useId();
  const open = expandable && expanded;
  return <section className="studio-section studio-disclosure" aria-label={title}>
    <h3 className="studio-disclosure-heading">
      {expandable ? <button type="button" aria-expanded={open} aria-controls={id} onClick={() => setExpanded(value => !value)}>
        <span>{title}</span>{open ? <ChevronUp size={16} aria-hidden="true"/> : <ChevronDown size={16} aria-hidden="true"/>}
      </button> : <span>{title}</span>}
    </h3>
    <div hidden={open}>{preview}
      {expandable && moreLabel && <button type="button" className="linklike studio-more" aria-expanded={open} aria-controls={id} onClick={() => setExpanded(true)}>
        <ChevronDown size={14} aria-hidden="true"/>{moreLabel}
      </button>}
    </div>
    <div id={id} hidden={!open}>{children}</div>
  </section>;
}
