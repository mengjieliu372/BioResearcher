const TOKEN_KEY = 'bioresearcher_auth_token';
const USER_KEY = 'bioresearcher_auth_user';
const WELCOME_KEY = 'bioresearcher_welcome_notice';

export const getAuthToken = () => localStorage.getItem(TOKEN_KEY) || '';

export const setAuthSession = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token || '');
  localStorage.setItem(USER_KEY, JSON.stringify(user || null));
};

export const clearAuthSession = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(WELCOME_KEY);
};

export const getAuthUser = () => {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
};

export const isLoggedIn = () => Boolean(getAuthToken());

export const setWelcomeNotice = (payload) => {
  if (!payload) return;
  const obj = typeof payload === 'string'
    ? { message: payload, isNewUser: false }
    : {
      message: String(payload.message || ''),
      isNewUser: Boolean(payload.isNewUser),
    };
  if (!obj.message) return;
  sessionStorage.setItem(WELCOME_KEY, JSON.stringify(obj));
};

export const consumeWelcomeNotice = () => {
  const raw = sessionStorage.getItem(WELCOME_KEY) || '';
  if (raw) {
    sessionStorage.removeItem(WELCOME_KEY);
  }
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return {
      message: String(parsed?.message || ''),
      isNewUser: Boolean(parsed?.isNewUser),
    };
  } catch {
    return { message: raw, isNewUser: false };
  }
};
