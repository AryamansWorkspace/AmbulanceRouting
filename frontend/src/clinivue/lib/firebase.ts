import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged, type User } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: "clinivue-d321c.firebaseapp.com",
  projectId: "clinivue-d321c",
  storageBucket: "clinivue-d321c.firebasestorage.app",
  messagingSenderId: "91980328524",
  appId: "1:91980328524:web:4de8b772120f36fe2e8ee9"
};

const app = initializeApp(firebaseConfig);
const auth = firebaseConfig.apiKey ? getAuth(app) : null;
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

export async function signInWithGoogle() {
  if (!auth) {
    throw new Error('Firebase authentication is not configured. Add VITE_FIREBASE_API_KEY to frontend/.env.');
  }

  const result = await signInWithPopup(auth, googleProvider);
  return result.user;
}

export async function logOut() {
  if (auth) {
    await signOut(auth);
  }
}

export function onAuthChange(callback: (user: User | null) => void) {
  if (!auth) {
    callback(null);
    return () => {};
  }

  return onAuthStateChanged(auth, callback);
}

export { auth, db };
export type { User };
