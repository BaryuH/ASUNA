import { useRef, useState } from 'react'
import { Image as ImageIcon, Search, Sparkles, Upload, Workflow, X } from 'lucide-react'

type Mode = 'semantic' | 'image' | 'skeleton'

const modes = [
  { id: 'semantic', label: 'Text', icon: Sparkles },
  { id: 'image', label: 'Image', icon: ImageIcon },
  { id: 'skeleton', label: 'Pose', icon: Workflow },
] as const

// Preview images only; these are not retrieval results.
const previewImages = [
  'photo-1506126613408-eca07ce68773',
  'photo-1544367567-0f2fcb009e0b',
  'photo-1506126613408-eca07ce68773',
  'photo-1518611012118-696072aa579a',
  'photo-1545205597-3d9d02c29597',
  'photo-1506126613408-eca07ce68773',
  'photo-1544367567-0f2fcb009e0b',
  'photo-1518611012118-696072aa579a',
  'photo-1545205597-3d9d02c29597',
  'photo-1544367567-0f2fcb009e0b',
  'photo-1518611012118-696072aa579a',
  'photo-1545205597-3d9d02c29597',
]

export default function Workstation() {
  const [mode, setMode] = useState<Mode>('semantic')
  const [query, setQuery] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [pose, setPose] = useState<File | null>(null)
  const [selectedImage, setSelectedImage] = useState<number | null>(null)
  const previewDialog = useRef<HTMLDialogElement>(null)
  const file = mode === 'image' ? image : pose

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="ASUNA home">asuna<span>.</span></a>
      </header>

      <div className="workspace">
        <aside className="sidebar" aria-label="Search controls">
          <div className="sidebar-intro">
            <span className="eyebrow">YOUR SEARCH</span>
            <h1>Find your pose<span>.</span></h1>
            <p>Start with a thought, an image, or a pose.</p>
          </div>

          <form onSubmit={(event) => event.preventDefault()}>
            <fieldset className="mode-field">
              <legend>Search by</legend>
              <div className="mode-list">
                {modes.map(({ id, label, icon: Icon }) => (
                  <label key={id} className={`mode-option mode-${id} ${mode === id ? 'is-selected' : ''}`}>
                    <input type="radio" name="mode" value={id} checked={mode === id} onChange={() => setMode(id)} />
                    <Icon size={17} aria-hidden="true" />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="query-field">
              {mode === 'semantic' ? (
                <>
                  <label htmlFor="query">Describe what you're looking for</label>
                  <textarea id="query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="A calm standing pose..." rows={5} />
                </>
              ) : (
                <>
                  <span className="field-label">{mode === 'image' ? 'Reference image' : 'Pose reference'}</span>
                  <label className="upload-box" htmlFor="reference">
                    <Upload size={20} aria-hidden="true" />
                    <strong>{file?.name || 'Choose an image'}</strong>
                    <span>Browse your files</span>
                  </label>
                  <input className="file-input" id="reference" type="file" accept="image/*" onChange={(event) => mode === 'image' ? setImage(event.target.files?.[0] ?? null) : setPose(event.target.files?.[0] ?? null)} />
                </>
              )}
            </div>
            <button className="run-button" type="submit" disabled><Search size={17} aria-hidden="true" /> Run search</button>
          </form>
        </aside>

        <main className="results" id="results">
          <div className="results-heading">
            <div><span className="eyebrow">EXPLORE</span><h2>Search results</h2><p className="preview-note">Preview images · not search results</p></div>
            <span className={`mode-tag mode-${mode}`}>{modes.find((item) => item.id === mode)?.label} search</span>
          </div>
          <div className="candidate-grid" aria-label="Sample candidate images">
            {previewImages.map((image, index) => (
              <button className={`candidate${index < 5 ? ` rank-${index + 1}` : ''}`} key={`${image}-${index}`} type="button" aria-label={`Preview sample image ${index + 1}${index < 5 ? `, rank ${index + 1}` : ''}`} onClick={() => { setSelectedImage(index); previewDialog.current?.showModal() }}>
                <img src={`https://images.unsplash.com/${image}?auto=format&fit=crop&w=480&q=80`} alt="" loading="lazy" />
                {index < 5 && <span className="rank-badge">#{index + 1}</span>}
              </button>
            ))}
          </div>
        </main>
      </div>
      <dialog ref={previewDialog} className="image-dialog" aria-label="Image preview" onClose={() => setSelectedImage(null)} onClick={(event) => { if (event.target === event.currentTarget) event.currentTarget.close() }}>
        <div className="preview-header"><span>Image preview</span><button type="button" className="close-preview" aria-label="Close preview" onClick={() => previewDialog.current?.close()}><X size={20} /></button></div>
        {selectedImage !== null && <img className="preview-image" src={`https://images.unsplash.com/${previewImages[selectedImage]}?auto=format&fit=max&w=1600&q=85`} alt={`Sample yoga image ${selectedImage + 1}`} />}
        <p className="preview-caption">Sample image · not a search result</p>
      </dialog>
    </div>
  )
}
