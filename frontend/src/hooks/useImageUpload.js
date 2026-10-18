import { useCallback, useEffect, useState } from 'react';
import { validateMediaFile } from '../utils/validators';

/** Manages a selected image/video file, its preview URL and validation error. */
export default function useImageUpload({ kind = 'image', maxMB = 8 } = {}) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [error, setError] = useState('');

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const select = useCallback((f) => {
    const err = validateMediaFile(f, { kind, maxMB });
    if (err) {
      setError(err);
      return false;
    }
    setError('');
    setFile(f);
    setPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(f);
    });
    return true;
  }, [kind, maxMB]);

  const clear = useCallback(() => {
    setFile(null);
    setError('');
    setPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return '';
    });
  }, []);

  return { file, preview, error, select, clear, setError, isVideo: !!file && file.type.startsWith('video/') };
}
