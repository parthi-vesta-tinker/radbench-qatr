/** State-specific panel controls matching the supplied NotebookLM references. */
export function PanelIcon({ side, collapsed = false }: { side: 'left' | 'right'; collapsed?: boolean }) {
  return <svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"
    className={`panel-symbol panel-symbol-${side}`} fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2.5" y="2.5" width="19" height="19" rx="5"/>
    {collapsed ? <>
      <path d="M7 8v8"/>
      <path d="m14.5 8.5-3.5 3.5 3.5 3.5"/>
    </> : <path d="M16.5 7.5v9"/>}
  </svg>;
}
