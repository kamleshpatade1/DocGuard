import { useEffect, useRef, useState } from 'react'
import {
  AlertCircle,
  ArrowDownUp,
  ArrowUpRight,
  Check,
  CheckCircle2,
  ChevronDown,
  Clipboard,
  Download,
  FileCode2,
  FileText,
  FolderOpen,
  LoaderCircle,
  RotateCcw,
  ScanSearch,
  ShieldCheck,
  Trash2,
  Upload,
  X,
} from 'lucide-react'
import './App.css'

const samples = {
  clean: {
    label: 'No drift',
    pythonName: 'students.py',
    markdownName: 'students.md',
    python: `def get_students(limit=30):
    """Return up to limit students."""
    return []

def add(left, right):
    return left + right
`,
    markdown: `# Student API

The default limit for \`get_students\` is 30.

Use \`add()\` to add two numbers.
`,
  },
  mismatch: {
    label: 'Default mismatch',
    pythonName: 'students.py',
    markdownName: 'students.md',
    python: `def get_students(limit=50):
    """Return up to limit students."""
    return []
`,
    markdown: `# Student API

The default limit for \`get_students\` is 30.
`,
  },
  missing: {
    label: 'Missing function',
    pythonName: 'math_utils.py',
    markdownName: 'math_utils.md',
    python: `def add(left, right):
    """Add two numbers."""
    return left + right
`,
    markdown: `# Math utilities

Use \`subtract()\` to find the difference between two values.
`,
  },
}

const initialInputs = {
  python: samples.mismatch.python,
  markdown: samples.mismatch.markdown,
  pythonName: samples.mismatch.pythonName,
  markdownName: samples.mismatch.markdownName,
  pythonUploaded: false,
  markdownUploaded: false,
  revision: 0,
}

const ruleDetails = {
  VALUE_MISMATCH: {
    title: 'Documented default differs from Python',
    description:
      'Compares a clearly stated Markdown parameter default with the literal default extracted from the matching Python function.',
    sample: 'mismatch',
  },
  FUNCTION_NOT_FOUND: {
    title: 'Documented function is not defined',
    description:
      'Finds simple call-shaped references in Markdown that do not match a top-level function or class method in the Python source.',
    sample: 'missing',
  },
}

const severityOrder = { high: 0, medium: 1, low: 2 }
const MAX_UPLOAD_BYTES = 800_000

function lineCount(value) {
  return value.split('\n').length
}

function App() {
  const [inputs, setInputs] = useState(initialInputs)
  const [scanState, setScanState] = useState('idle')
  const [lastScan, setLastScan] = useState(null)
  const [notice, setNotice] = useState(null)
  const [ruleFilter, setRuleFilter] = useState('all')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('severity')
  const [jumpTarget, setJumpTarget] = useState(null)
  const isScanning = scanState === 'loading'
  const hasInputs = Boolean(inputs.python.trim() && inputs.markdown.trim())
  const scanIsStale = lastScan && lastScan.revision !== inputs.revision
  const findings = lastScan?.findings ?? []

  function updateInputs(update) {
    setInputs((current) => ({ ...current, ...update, revision: current.revision + 1 }))
  }

  function loadSample(sampleName) {
    const sample = samples[sampleName]
    updateInputs({
      python: sample.python,
      markdown: sample.markdown,
      pythonName: sample.pythonName,
      markdownName: sample.markdownName,
      pythonUploaded: false,
      markdownUploaded: false,
    })
    setNotice({ type: 'success', text: `${sample.label} sample loaded.` })
  }

  function resetDefaults() {
    setInputs((current) => ({
      ...initialInputs,
      revision: current.revision + 1,
    }))
    setNotice({ type: 'success', text: 'Inputs reset to the default sample.' })
  }

  function clearInputs() {
    updateInputs({
      python: '',
      markdown: '',
      pythonName: 'source.py',
      markdownName: 'README.md',
      pythonUploaded: false,
      markdownUploaded: false,
    })
    setNotice({ type: 'info', text: 'Both editor inputs are clear.' })
  }

  async function loadFile(file, kind) {
    if (!file) return
    const isPython = kind === 'python'
    const supported = isPython
      ? file.name.toLowerCase().endsWith('.py')
      : /\.(md|markdown)$/i.test(file.name)
    if (!supported) {
      setNotice({
        type: 'error',
        text: isPython
          ? 'Choose a Python file with the .py extension.'
          : 'Choose a Markdown file with the .md or .markdown extension.',
      })
      return
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setNotice({ type: 'error', text: 'Each uploaded file must be smaller than 800 KB.' })
      return
    }
    try {
      const contents = await file.text()
      if (!contents.trim()) {
        setNotice({ type: 'error', text: `${file.name} is empty. Choose a file with content.` })
        return
      }
      updateInputs(
        isPython
          ? { python: contents, pythonName: file.name, pythonUploaded: true }
          : { markdown: contents, markdownName: file.name, markdownUploaded: true },
      )
      setNotice({ type: 'success', text: `${file.name} loaded. You can still edit its text.` })
    } catch {
      setNotice({ type: 'error', text: `Could not read ${file.name}. Try another file.` })
    }
  }

  function removeFile(kind) {
    updateInputs(
      kind === 'python'
        ? { pythonName: 'source.py', pythonUploaded: false }
        : { markdownName: 'README.md', markdownUploaded: false },
    )
    setNotice({ type: 'info', text: 'File label removed; editor text was kept.' })
  }

  async function scanForDrift() {
    if (!hasInputs || isScanning) return
    const scanInputs = inputs
    setScanState('loading')
    setNotice({ type: 'info', text: 'Scanning with the DocGuard engine…' })

    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documentation: scanInputs.markdown,
          python_source: scanInputs.python,
          documentation_filename: scanInputs.markdownName,
          python_filename: scanInputs.pythonName,
        }),
      })
      const result = await response.json()
      if (!response.ok) {
        throw new Error(result.error || `The scan failed (${response.status}).`)
      }
      if (!Array.isArray(result.findings)) {
        throw new Error('The scanner returned an unexpected response.')
      }

      setLastScan({
        findings: result.findings,
        revision: scanInputs.revision,
        scannedAt: new Date().toISOString(),
      })
      setScanState('success')
      setNotice({
        type: result.findings.length ? 'warning' : 'success',
        text: result.findings.length
          ? `Scan complete: ${result.findings.length} finding${result.findings.length === 1 ? '' : 's'} detected.`
          : 'Scan complete: no drift found in the supported checks.',
      })
    } catch (scanError) {
      setScanState('error')
      setNotice({
        type: 'error',
        text:
          scanError instanceof TypeError
            ? 'Could not connect to the DocGuard API. Check that the Flask server is running.'
            : scanError instanceof Error
              ? scanError.message
              : 'The scan failed unexpectedly. Please try again.',
      })
    }
  }

  function handleWorkspaceKeyDown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
      event.preventDefault()
      scanForDrift()
    }
  }

  function navigateToLine(kind, line, fileName) {
    setJumpTarget({ kind, line, token: Date.now() })
    document.getElementById(`${kind}-editor`)?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })
    setNotice({
      type: 'info',
      text: `Jumped to line ${line} in ${fileName || (kind === 'python' ? 'Python source' : 'documentation')}.`,
    })
  }

  async function copyFinding(finding) {
    const details = [
      finding.rule_id,
      finding.title,
      finding.message,
      `Documentation: ${(finding.documentation_locations || []).map((item) => `${item.file}:${item.line}`).join(', ')}`,
      `Python: ${finding.evidence_file || 'source'}${finding.evidence_line ? `:${finding.evidence_line}` : ''}`,
      `Confidence: ${finding.confidence}`,
    ].join('\n')
    try {
      await navigator.clipboard.writeText(details)
      setNotice({ type: 'success', text: 'Finding details copied to clipboard.' })
    } catch {
      setNotice({ type: 'error', text: 'Clipboard access was unavailable in this browser.' })
    }
  }

  function downloadResults() {
    if (!lastScan) return
    const json = JSON.stringify(
      {
        scanned_at: lastScan.scannedAt,
        scan_status: lastScan.findings.length ? 'findings_detected' : 'clean',
        total_findings: lastScan.findings.length,
        findings: lastScan.findings,
      },
      null,
      2,
    )
    const url = URL.createObjectURL(new Blob([json], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'docguard-scan-results.json'
    link.click()
    URL.revokeObjectURL(url)
  }

  const filteredFindings = sortFindings(
    findings.filter((finding) => {
      const matchesRule = ruleFilter === 'all' || finding.rule_id === ruleFilter
      const matchesSeverity =
        severityFilter === 'all' || finding.severity === severityFilter
      const query = search.trim().toLowerCase()
      const matchesSearch =
        !query ||
        `${finding.function_name || ''} ${finding.message} ${finding.rule_id}`
          .toLowerCase()
          .includes(query)
      return matchesRule && matchesSeverity && matchesSearch
    }),
    sortBy,
  )

  const highCount = findings.filter((finding) => finding.severity === 'high').length
  const mediumCount = findings.filter((finding) => finding.severity === 'medium').length
  const statusLabel = isScanning
    ? 'Scanning'
    : scanState === 'error'
      ? 'Scan failed'
      : lastScan
        ? lastScan.findings.length
          ? 'Drift detected'
          : 'No drift'
        : 'Not scanned'

  return (
    <div className="app-shell" onKeyDown={handleWorkspaceKeyDown}>
      <aside className="sidebar">
        <a className="brand" href="#scanner" aria-label="DocGuard home">
          <span className="brand-mark"><ShieldCheck size={21} strokeWidth={2.2} /></span>
          <span>DocGuard</span>
        </a>
        <div className="sidebar-label">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          <a className="nav-item active" href="#scanner"><ScanSearch size={18} /><span>Drift scanner</span></a>
          <a className="nav-item" href="#rule-guide"><ShieldCheck size={18} /><span>Rule guide</span></a>
        </nav>
        <div className="sidebar-spacer" />
        <div className="sidebar-note">
          <div className="sidebar-note-icon"><ShieldCheck size={17} /></div>
          <strong>Private by design</strong>
          <p>Source is analyzed locally by your DocGuard server and never executed.</p>
        </div>
        <div className="sidebar-footer"><span className="status-dot" />Local workspace</div>
      </aside>

      <main className="main-content" id="scanner">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>Drift scanner</strong></div>
          <div className={`engine-pill engine-${scanState}`}><span className="status-dot" />{statusLabel}</div>
        </header>

        <div className="workspace">
          <section className="page-heading">
            <div>
              <div className="eyebrow">DOCUMENTATION QUALITY</div>
              <h1>Find drift before your users do.</h1>
              <p>Compare what your docs promise with what your Python code actually does.</p>
            </div>
            <div className="heading-icon"><ScanSearch size={25} /></div>
          </section>

          <section className="sample-toolbar" aria-label="Sample projects">
            <div className="sample-label"><FolderOpen size={15} /> Try a sample</div>
            {Object.entries(samples).map(([key, sample]) => (
              <button className="sample-button" key={key} onClick={() => loadSample(key)}>
                {sample.label}
              </button>
            ))}
            <span className="toolbar-spacer" />
            <button className="subtle-button" onClick={clearInputs}><Trash2 size={14} />Clear</button>
            <button className="subtle-button" onClick={resetDefaults}><RotateCcw size={14} />Reset defaults</button>
          </section>

          <section className="editor-grid" aria-label="Scan inputs">
            <CodeEditor
              id="python"
              label="Python source"
              filename={inputs.pythonName}
              uploaded={inputs.pythonUploaded}
              value={inputs.python}
              onChange={(value) => updateInputs({ python: value })}
              onUpload={(file) => loadFile(file, 'python')}
              onRemove={() => removeFile('python')}
              uploadAccept=".py"
              description="Python is parsed by the existing AST engine, never executed."
              jumpTarget={jumpTarget}
            />
            <CodeEditor
              id="markdown"
              label="Documentation"
              filename={inputs.markdownName}
              uploaded={inputs.markdownUploaded}
              value={inputs.markdown}
              onChange={(value) => updateInputs({ markdown: value })}
              onUpload={(file) => loadFile(file, 'markdown')}
              onRemove={() => removeFile('markdown')}
              uploadAccept=".md,.markdown"
              description="Paste or upload a Markdown file. The text remains editable."
              jumpTarget={jumpTarget}
            />
          </section>

          <div className="action-row">
            <div className="input-hint"><span className="hint-dot" />{hasInputs ? 'Press Ctrl/⌘ + Enter to scan' : 'Both editors need content before scanning'}</div>
            <button className="scan-button" onClick={scanForDrift} disabled={isScanning || !hasInputs}>
              {isScanning ? <LoaderCircle className="spin" size={17} /> : <ScanSearch size={17} />}
              {isScanning ? 'Scanning…' : lastScan ? 'Rescan' : 'Scan for drift'}
              {!isScanning && <ArrowUpRight size={16} />}
            </button>
          </div>

          {notice && (
            <div className={`notice notice-${notice.type}`} role={notice.type === 'error' ? 'alert' : 'status'}>
              {notice.type === 'error' ? <AlertCircle size={17} /> : notice.type === 'success' ? <CheckCircle2 size={17} /> : <ShieldCheck size={17} />}
              <span>{notice.text}</span>
              <button aria-label="Dismiss notification" onClick={() => setNotice(null)}><X size={15} /></button>
            </div>
          )}

          <section className="results-section" aria-live="polite">
            <div className="results-heading">
              <div>
                <div className="section-title">Scan overview</div>
                <div className="section-subtitle">
                  {lastScan
                    ? `${new Date(lastScan.scannedAt).toLocaleString()}${scanIsStale ? ' · Inputs changed since this scan' : ''}`
                    : 'Run a scan to review evidence-backed findings'}
                </div>
              </div>
              <button className="outline-button" onClick={downloadResults} disabled={!lastScan}>
                <Download size={15} />Export JSON
              </button>
            </div>

            <div className="stats-grid">
              <StatCard label="Total findings" value={lastScan ? findings.length : '—'} icon={<ScanSearch size={17} />} tone="purple" />
              <StatCard label="High severity" value={lastScan ? highCount : '—'} icon={<AlertCircle size={17} />} tone="red" />
              <StatCard label="Medium severity" value={lastScan ? mediumCount : '—'} icon={<AlertCircle size={17} />} tone="amber" />
              <StatCard label="Scan status" value={statusLabel} icon={scanState === 'error' ? <AlertCircle size={17} /> : <CheckCircle2 size={17} />} tone={scanState === 'error' ? 'red' : 'green'} compact />
            </div>

            {isScanning && (
              <div className="state-card loading-state"><LoaderCircle className="spin" size={19} />Analyzing current editor contents…</div>
            )}
            {scanState === 'error' && (
              <div className="state-card error-state"><AlertCircle size={19} /><div><strong>Latest scan failed</strong><p>{lastScan ? 'Your previous successful results are kept below; no success was recorded for this request.' : 'No successful scan is recorded for these inputs yet.'}</p></div></div>
            )}
            {lastScan && !findings.length && !isScanning && scanState !== 'error' && (
              <div className="state-card clear-state"><CheckCircle2 size={20} /><div><strong>No drift detected</strong><p>Your documentation matches the supported checks in this source.</p></div></div>
            )}

            {lastScan && findings.length > 0 && (
              <>
                <div className="finding-toolbar">
                  <div className="filter-tabs" role="group" aria-label="Filter findings by rule">
                    {[
                      ['all', 'All'],
                      ['VALUE_MISMATCH', 'Value mismatch'],
                      ['FUNCTION_NOT_FOUND', 'Missing function'],
                    ].map(([value, label]) => (
                      <button
                        key={value}
                        className={ruleFilter === value ? 'filter-tab selected' : 'filter-tab'}
                        aria-pressed={ruleFilter === value}
                        onClick={() => setRuleFilter(value)}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                  <div className="finding-controls">
                    <label className="search-field">
                      <ScanSearch size={15} />
                      <input aria-label="Search findings" placeholder="Search findings" value={search} onChange={(event) => setSearch(event.target.value)} />
                    </label>
                    <label className="select-control">
                      <span className="visually-hidden">Filter by severity</span>
                      <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>
                        <option value="all">All severity</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                      <ChevronDown size={14} />
                    </label>
                    <label className="select-control sort-control">
                      <ArrowDownUp size={14} />
                      <span className="visually-hidden">Sort findings</span>
                      <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
                        <option value="severity">Severity</option>
                        <option value="source-line">Source line</option>
                      </select>
                      <ChevronDown size={14} />
                    </label>
                  </div>
                </div>

                {filteredFindings.length ? (
                  <div className="finding-list">
                    {filteredFindings.map((finding, index) => (
                      <FindingCard
                        finding={finding}
                        key={`${finding.rule_id}-${finding.message}-${index}`}
                        onCopy={() => copyFinding(finding)}
                        onNavigate={navigateToLine}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="state-card filtered-empty">No findings match these filters. Try changing the rule, severity, or search.</div>
                )}
              </>
            )}
          </section>

          <section className="rule-guide" id="rule-guide">
            <div className="guide-heading">
              <div><div className="section-title">Rule guide</div><div className="section-subtitle">What DocGuard checks today</div></div>
            </div>
            <div className="rule-grid">
              {Object.entries(ruleDetails).map(([ruleId, rule]) => (
                <article className="rule-card" key={ruleId}>
                  <div className="rule-card-top"><span className="rule-icon"><ShieldCheck size={17} /></span><span className="rule-id">{ruleId}</span></div>
                  <h3>{rule.title}</h3>
                  <p>{rule.description}</p>
                  <button className="text-button" onClick={() => loadSample(rule.sample)}>Try this rule<ArrowUpRight size={14} /></button>
                </article>
              ))}
            </div>
          </section>

          <footer className="page-footer">DocGuard checks explicit patterns and reports evidence for developer review.</footer>
        </div>
      </main>
    </div>
  )
}

function CodeEditor({
  id,
  label,
  filename,
  uploaded,
  value,
  onChange,
  onUpload,
  onRemove,
  uploadAccept,
  description,
  jumpTarget,
}) {
  const textareaRef = useRef(null)
  const gutterRef = useRef(null)
  const fileInputRef = useRef(null)
  const lines = value.split('\n')
  const lineTotal = lineCount(value)
  const activeLine = jumpTarget?.kind === id ? jumpTarget.line : null

  useEffect(() => {
    if (!activeLine || !jumpTarget?.token) return
    const textarea = textareaRef.current
    if (!textarea) return
    const currentLines = value.split('\n')
    const boundedLine = Math.max(1, Math.min(activeLine, currentLines.length))
    const start = currentLines
      .slice(0, boundedLine - 1)
      .reduce((sum, item) => sum + item.length + 1, 0)
    const end = start + (currentLines[boundedLine - 1]?.length ?? 0)
    textarea.focus()
    textarea.setSelectionRange(start, end)
    textarea.scrollTop = (boundedLine - 1) * Number.parseFloat(getComputedStyle(textarea).lineHeight)
    if (gutterRef.current) gutterRef.current.scrollTop = textarea.scrollTop
  }, [activeLine, jumpTarget?.token, value])

  return (
    <section className="editor-card" id={`${id}-editor`} aria-label={label}>
      <header className="editor-card-header">
        <div className="editor-file-title">
          <span className="editor-label">{id === 'python' ? <FileCode2 size={17} /> : <FileText size={17} />}{label}</span>
          <span className="file-name" title={filename}>{filename}</span>
          {uploaded && <span className="uploaded-tag">uploaded</span>}
        </div>
        <div className="file-actions">
          {uploaded && <button className="icon-button remove-file" onClick={onRemove} aria-label={`Remove ${filename} file label`} title="Remove uploaded file"><X size={15} /></button>}
          <button className="upload-button" onClick={() => fileInputRef.current?.click()}><Upload size={14} />Upload</button>
          <input
            ref={fileInputRef}
            className="visually-hidden"
            type="file"
            accept={uploadAccept}
            aria-label={`Upload ${label} file`}
            onChange={(event) => {
              onUpload(event.target.files?.[0])
              event.target.value = ''
            }}
          />
        </div>
      </header>
      <p className="editor-description">{description}</p>
      <div className="code-editor">
        <div className="line-gutter" ref={gutterRef} aria-hidden="true">
          {lines.map((_, index) => (
            <span className={activeLine === index + 1 ? 'line-number active-line' : 'line-number'} key={index}>{index + 1}</span>
          ))}
        </div>
        <textarea
          ref={textareaRef}
          id={`${id}-textarea`}
          spellCheck="false"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onScroll={(event) => {
            if (gutterRef.current) gutterRef.current.scrollTop = event.currentTarget.scrollTop
          }}
          aria-label={label}
          aria-describedby={`${id}-editor-stats`}
          wrap="off"
        />
      </div>
      <footer className="editor-footer" id={`${id}-editor-stats`}>
        <span className="editor-dot" />Editable
        <span className="editor-stat">{value.length.toLocaleString()} chars</span>
        <span className="editor-stat">{lineTotal} lines</span>
        {activeLine && <span className="jump-indicator">Line {activeLine} selected</span>}
      </footer>
    </section>
  )
}

function StatCard({ label, value, icon, tone, compact = false }) {
  return (
    <article className={`stat-card stat-${tone}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-copy"><span>{label}</span><strong className={compact ? 'stat-status' : ''}>{value}</strong></div>
    </article>
  )
}

function FindingCard({ finding, onCopy, onNavigate }) {
  const locations = finding.documentation_locations?.length
    ? finding.documentation_locations
    : [{ file: finding.documentation_file, line: finding.documentation_line, text: finding.documented_text }]

  return (
    <details className="finding-card">
      <summary className="finding-summary">
        <span className="finding-symbol"><AlertCircle size={19} /></span>
        <span className="finding-summary-main">
          <span className="finding-topline">
            <span className="rule-name">{finding.rule_id}</span>
            <span className={`severity severity-${finding.severity}`}>{finding.severity} severity</span>
          </span>
          <strong>{finding.function_name || finding.title}</strong>
          <span className="finding-message">{finding.message}</span>
          <span className="finding-locations">
            <span><FileText size={14} />{locations.length > 1 ? `${locations.length} documentation locations` : `${locations[0].file}:${locations[0].line}`}</span>
            <span><FileCode2 size={14} />{finding.evidence_file || 'Python source'}{finding.evidence_line ? `:${finding.evidence_line}` : ''}</span>
          </span>
        </span>
        <span className={`confidence confidence-${finding.confidence}`}>{finding.confidence} confidence</span>
        <ChevronDown className="expand-chevron" size={16} />
      </summary>
      <div className="finding-details">
        <div className="detail-heading"><strong>Finding details</strong><button className="copy-button" onClick={onCopy}><Clipboard size={14} />Copy details</button></div>
        <div className="detail-rule"><span>Rule</span><code>{finding.rule_id}</code><strong>{finding.title}</strong></div>
        <p className="detail-message">{finding.message}</p>
        <div className="detail-columns">
          <div className="detail-block">
            <span className="detail-label">DOCUMENTATION</span>
            {locations.map((location) => (
              <div className="detail-location" key={`${location.file}-${location.line}-${location.text}`}>
                <p>{location.text}</p>
                <button onClick={() => onNavigate('markdown', location.line, location.file)}>
                  <FileText size={14} />{location.file}:{location.line}<ArrowUpRight size={13} />
                </button>
              </div>
            ))}
          </div>
          <div className="detail-block">
            <span className="detail-label">PYTHON EVIDENCE</span>
            <p>{finding.evidence_text || 'No matching Python definition was found.'}</p>
            {finding.evidence_line ? (
              <button onClick={() => onNavigate('python', finding.evidence_line, finding.evidence_file)}>
                <FileCode2 size={14} />{finding.evidence_file}:{finding.evidence_line}<ArrowUpRight size={13} />
              </button>
            ) : <span className="no-source-line">No matching source line</span>}
          </div>
        </div>
        <div className="detail-confidence"><Check size={14} />Evidence confidence: <strong>{finding.confidence}</strong></div>
      </div>
    </details>
  )
}

function sortFindings(findings, sortBy) {
  return [...findings].sort((left, right) => {
    if (sortBy === 'source-line') {
      return (left.evidence_line ?? Number.MAX_SAFE_INTEGER) - (right.evidence_line ?? Number.MAX_SAFE_INTEGER)
    }
    return (severityOrder[left.severity] ?? 3) - (severityOrder[right.severity] ?? 3)
  })
}

export default App
