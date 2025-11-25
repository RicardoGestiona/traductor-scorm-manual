/**
 * Componente raíz de la aplicación.
 *
 * Filepath: frontend/src/App.tsx
 * Feature alignment: STORY-003 - Setup Frontend React
 */

import { Layout } from './components/Layout';
import { Home } from './pages/Home';

function App() {
  return (
    <Layout>
      <Home />
    </Layout>
  );
}

export default App;
