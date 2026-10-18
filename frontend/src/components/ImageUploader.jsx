import { useRef, useState } from 'react';
import { UploadCloud, X, RefreshCw } from 'lucide-react';
import Button from './Button';

/**
 * Drag & drop + click-to-browse uploader with live preview and validation errors.
 * Controlled by the `useImageUpload` hook (preview, error, select, clear).
 */
export default function ImageUploader({
  preview, error, onSelect, onClear, accept = 'image/*', title = 'Upload Food Image',
  hint = 'Drag and drop or click to upload', note, disabled, buttonLabel = 'Choose File', buttonVariant = 'accent', isVideo = false,
}) {
  const inputRef = useRef(null);
  const [drag, setDrag] = useState(false);

  const openPicker = () => !disabled && inputRef.current?.click();
  const handleFiles = (files) => {
    if (files && files[0]) onSelect(files[0]);
  };

  return (
    <div className="uploader-wrap">
      <div
        className={`uploader ${drag ? 'uploader--drag' : ''} ${preview ? 'uploader--has' : ''} ${error ? 'uploader--error' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); handleFiles(e.dataTransfer.files); }}
        onClick={!preview ? openPicker : undefined}
        role={!preview ? 'button' : undefined}
        tabIndex={!preview ? 0 : undefined}
        onKeyDown={(e) => { if (!preview && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openPicker(); } }}
        aria-label={!preview ? title : undefined}
      >
        <input
          ref={inputRef} type="file" accept={accept} hidden
          onChange={(e) => { handleFiles(e.target.files); e.target.value = ''; }}
        />
        {preview ? (
          <div className="uploader__preview">
            {isVideo
              ? <video src={preview} controls muted playsInline aria-label="Selected video preview" />
              : <img src={preview} alt="Selected upload preview" />}
            <div className="uploader__actions">
              <button type="button" className="chip-btn" onClick={(e) => { e.stopPropagation(); openPicker(); }}>
                <RefreshCw size={14} /> Replace
              </button>
              <button type="button" className="chip-btn chip-btn--danger" onClick={(e) => { e.stopPropagation(); onClear(); }}>
                <X size={14} /> Remove
              </button>
            </div>
          </div>
        ) : (
          <>
            <span className="uploader__icon"><UploadCloud size={28} /></span>
            <strong>{title}</strong>
            <span className="uploader__hint">{hint}</span>
            <Button variant={buttonVariant} size="sm" onClick={(e) => { e.stopPropagation(); openPicker(); }} disabled={disabled}>
              {buttonLabel}
            </Button>
            {note && <span className="uploader__note">{note}</span>}
          </>
        )}
      </div>
      {error && <p className="field__error" role="alert">{error}</p>}
    </div>
  );
}
