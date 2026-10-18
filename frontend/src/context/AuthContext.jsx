import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { loadJSON, saveJSON, sleep } from '../utils/helpers';

const AuthContext = createContext(null);

const USERS_KEY = 'fv_users';
const SESSION_KEY = 'fv_session';

// Demo account so reviewers can sign in immediately.
export const DEMO_USER = { name: 'Akanksha', email: 'akanksha@example.com', password: 'FoodVerse1' };

function getUsers() {
  const users = loadJSON(USERS_KEY, []);
  if (!users.some((u) => u.email === DEMO_USER.email)) users.push(DEMO_USER);
  return users;
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => loadJSON(SESSION_KEY, null));

  const persist = (user) => {
    const s = { name: user.name, email: user.email };
    setSession(s);
    saveJSON(SESSION_KEY, s);
    return s;
  };

  const login = useCallback(async ({ email, password }) => {
    await sleep(700);
    const user = getUsers().find((u) => u.email.toLowerCase() === email.trim().toLowerCase());
    if (!user) throw new Error('No account found with this email. Try signing up first.');
    if (user.password !== password) throw new Error('Incorrect password. Please try again.');
    return persist(user);
  }, []);

  const signup = useCallback(async ({ name, email, password }) => {
    await sleep(800);
    const users = getUsers();
    if (users.some((u) => u.email.toLowerCase() === email.trim().toLowerCase())) {
      throw new Error('An account with this email already exists. Try logging in.');
    }
    const user = { name: name.trim(), email: email.trim(), password };
    saveJSON(USERS_KEY, [...users, user]);
    return persist(user);
  }, []);

  const changePassword = useCallback(async ({ current, next }) => {
    await sleep(600);
    const users = getUsers();
    const me = users.find((u) => u.email === session?.email);
    if (!me) throw new Error('Account not found. Please log in again.');
    if (me.password !== current) throw new Error('Current password is incorrect.');
    saveJSON(USERS_KEY, users.map((u) => (u.email === me.email ? { ...u, password: next } : u)));
  }, [session]);

  const loginAsDemo = useCallback(async () => {
    await sleep(500);
    return persist(DEMO_USER);
  }, []);

  const logout = useCallback(() => {
    setSession(null);
    try { localStorage.removeItem(SESSION_KEY); } catch { /* ignore */ }
  }, []);

  const updateSession = useCallback((patch) => {
    setSession((s) => {
      const next = { ...s, ...patch };
      saveJSON(SESSION_KEY, next);
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ user: session, isAuthed: !!session, login, signup, loginAsDemo, logout, updateSession, changePassword }),
    [session, login, signup, loginAsDemo, logout, updateSession, changePassword],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
