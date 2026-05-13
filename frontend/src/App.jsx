// frontend/src/App.jsx
// Root app component with routing.
// React Router wraps all pages.

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App