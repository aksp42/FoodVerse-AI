const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export function validateEmail(value) {
  if (!value?.trim()) return 'Email is required';
  if (!EMAIL_RE.test(value.trim())) return 'Enter a valid email address';
  return '';
}

export function validatePassword(value) {
  if (!value) return 'Password is required';
  if (value.length < 8) return 'Use at least 8 characters';
  if (!/[A-Za-z]/.test(value) || !/\d/.test(value)) return 'Include at least one letter and one number';
  return '';
}

export function validateName(value) {
  if (!value?.trim()) return 'Name is required';
  if (value.trim().length < 2) return 'Name is too short';
  return '';
}

export function validatePhone(value) {
  if (!value?.trim()) return '';
  if (!/^[+\d][\d\s-]{6,16}$/.test(value.trim())) return 'Enter a valid phone number';
  return '';
}

export function passwordStrength(value = '') {
  let score = 0;
  if (value.length >= 8) score++;
  if (/[A-Z]/.test(value) && /[a-z]/.test(value)) score++;
  if (/\d/.test(value)) score++;
  if (/[^A-Za-z0-9]/.test(value)) score++;
  return score; // 0–4
}

/** kind: 'image' (default) or 'media' (image or video). */
export function validateMediaFile(file, { kind = 'image', maxMB = 8 } = {}) {
  if (!file) return 'No file selected';
  const isImage = file.type.startsWith('image/');
  const isVideo = file.type.startsWith('video/');
  if (kind === 'image' && !isImage) return 'Please choose an image file (JPG, PNG or WebP)';
  if (kind === 'media' && !isImage && !isVideo) return 'Please choose an image or video file';
  const limit = isVideo ? Math.max(maxMB, 50) : maxMB;
  if (file.size > limit * 1024 * 1024) return `File is too large. Max size is ${limit} MB`;
  return '';
}

export const validateImageFile = (file, maxMB = 8) => validateMediaFile(file, { kind: 'image', maxMB });
