/**
 * Componente raíz de la aplicación con routing y autenticación.
 *
 * Filepath: frontend/src/App.tsx
 * Feature alignment: STORY-003 - Setup Frontend React, STORY-017 - Autenticación
 */

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { Layout } from './components/Layout';
import { Home } from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </Router>
  );
}

export default App;
