import { getAuth, GoogleAuthProvider, onAuthStateChanged, signInWithPopup, signOut } from "firebase/auth";
import { initializeApp } from "firebase/app";

const apiKey = import.meta.env.VITE_FIREBASE_API_KEY;

const firebaseConfig = {
  apiKey,
  authDomain: "clinivue-d321c.firebaseapp.com",
  projectId: "clinivue-d321c",
  storageBucket: "clinivue-d321c.firebasestorage.app",
  messagingSenderId: "91980328524",
  appId: "1:91980328524:web:4de8b772120f36fe2e8ee9",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export function signInWithGoogle() {
  if (!apiKey) {
    throw new Error(
      "Firebase authentication is not configured. Add VITE_FIREBASE_API_KEY to frontend/.env."
    );
  }

  return signInWithPopup(auth, googleProvider);
}

export function logOut() {
  return signOut(auth);
}

export function onAuthChange(callback) {
  return onAuthStateChanged(auth, callback);
}
